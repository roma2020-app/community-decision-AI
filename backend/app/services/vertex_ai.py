import logging
from typing import List, Dict, Any
from app.config import GCP_PROJECT, GCP_LOCATION, GEMINI_MODEL, SIMULATION_MODE

logger = logging.getLogger(__name__)

# Vertex AI Initialization
vertex_initialized = False
generative_model = None

if GCP_PROJECT and not SIMULATION_MODE:
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, SafetySetting
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
        generative_model = GenerativeModel(GEMINI_MODEL)
        vertex_initialized = True
        logger.info(f"Vertex AI initialized with project '{GCP_PROJECT}' and model '{GEMINI_MODEL}'")
    except Exception as e:
        logger.warning(f"Failed to initialize Vertex AI: {str(e)}. Falling back to simulation mode.")
else:
    logger.info("Running in simulation mode (No GCP_PROJECT provided or SIMULATION_MODE=true).")

# ==========================================
# Prompt Templates & Context Builders
# ==========================================

SYSTEM_PROMPT = """You are the AI-powered Community Decision Intelligence Platform Assistant. 
Your goal is to assist city planners, municipal authorities, and community leaders by analyzing local indicators 
(Complaints, Traffic Density, and Air Quality Index) to answer policy and urban management questions.

Here is the current structured community data context loaded directly from AlloyDB:
{data_context}

Guidelines:
1. Base your analysis on the provided community data context first.
2. If the user asks for areas needing attention or highest risk:
   - AQI: Values > 100 are Unhealthy, > 150 are Dangerous.
   - Complaints: High numbers indicate municipal bottlenecks.
   - Traffic: High density represents severe congestion.
3. Be professional, direct, and suggest realistic urban planning recommendations.
4. If the data context is empty, guide the user to upload a CSV file first.
"""

def format_db_context(records: List[Any]) -> str:
    """Format SQLAlchemy CommunityData models into structured context text for Gemini."""
    if not records:
        return "No community records are currently indexed in AlloyDB."
        
    context_lines = []
    for r in records:
        timestamp_str = r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "N/A"
        context_lines.append(
            f"Neighborhood: {r.area}\n"
            f" - Complaints count: {r.complaints}\n"
            f" - Traffic Density: {r.traffic}\n"
            f" - Air Quality Index (AQI): {r.aqi}\n"
            f" - Last Updated: {timestamp_str}\n"
        )
    return "\n".join(context_lines)

# ==========================================
# Service Interfaces
# ==========================================

def get_gemini_response(db_records: List[Any], question: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Generate response from Gemini model using Vertex AI.
    Falls back to high-fidelity simulation if Vertex AI is not initialized.
    """
    # 1. Format the database context
    data_context = format_db_context(db_records)
    
    # 2. Complete prompt formulation
    system_text = SYSTEM_PROMPT.format(data_context=data_context)
    
    if vertex_initialized and generative_model:
        try:
            # Build history list in Vertex AI format
            # Vertex AI content structure: list of parts/history
            # For simplicity, we append system instruction and chat history into prompt context
            full_prompt = f"{system_text}\n\n"
            
            if chat_history:
                full_prompt += "Conversation history:\n"
                for msg in chat_history:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += "\n"
                
            full_prompt += f"Current Question: {question}\nAssistant:"
            
            response = generative_model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error calling Vertex AI API: {str(e)}")
            # Fall through to simulation if API fails in-flight
            pass

    # 3. High-fidelity Semantic Simulation Fallback
    return simulate_gemini_response(db_records, question, chat_history)


# ==========================================
# High-Fidelity Simulation Engine
# ==========================================

def simulate_gemini_response(db_records: List[Any], question: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Simulates Gemini's analysis by inspecting the database records and answering
    semantically based on actual indicators.
    """
    q_lower = question.lower()
    
    if not db_records:
        return (
            "Hello! I am your Community Decision Intelligence Assistant. "
            "Currently, there is no community data stored in AlloyDB. "
            "Please navigate to the **Data Upload** page in the sidebar and upload a community CSV dataset so I can analyze it for you."
        )

    # 1. Compute summary statistics for simulation
    total_complaints = sum(r.complaints for r in db_records)
    highest_complaints_rec = max(db_records, key=lambda r: r.complaints) if db_records else None
    highest_aqi_rec = max(db_records, key=lambda r: r.aqi) if db_records else None
    
    high_traffic_areas = [r.area for r in db_records if r.traffic.lower() == "high"]
    high_aqi_areas = [r.area for r in db_records if r.aqi > 100]
    high_complaints_areas = [r.area for r in db_records if r.complaints > 15]

    # Calculate general risk priority score (combination of complaints, high traffic, and AQI)
    # Area risk score = complaints + (aqi * 0.2) + (50 if traffic is high)
    def compute_risk_score(r):
        score = r.complaints + (r.aqi * 0.2)
        if r.traffic.lower() == "high":
            score += 50
        elif r.traffic.lower() == "medium":
            score += 20
        return score

    highest_risk_rec = max(db_records, key=compute_risk_score) if db_records else None

    # 2. Match intent and construct response
    # Intent A: Wards/Areas needing attention
    if any(k in q_lower for k in ["attention", "priority", "critical", "need help", "bad"]):
        response = (
            "### 🚨 Neighborhoods Requiring Immediate Attention\n\n"
            f"Based on the analysis of **{len(db_records)}** records, the following areas require municipal priority:\n\n"
        )
        
        needs_attention = False
        if highest_aqi_rec and highest_aqi_rec.aqi > 100:
            needs_attention = True
            response += f"1. **{highest_aqi_rec.area}** is reporting an unhealthy AQI of **{highest_aqi_rec.aqi}**. We recommend air quality sensors deployment.\n"
        if highest_complaints_rec and highest_complaints_rec.complaints > 15:
            needs_attention = True
            response += f"2. **{highest_complaints_rec.area}** has a high volume of community complaints (**{highest_complaints_rec.complaints}** open issues).\n"
        if high_traffic_areas:
            needs_attention = True
            response += f"3. **{', '.join(high_traffic_areas)}** show High Traffic Density, causing congestion and microparticle pollution.\n"

        if not needs_attention:
            response += "All analyzed wards are currently within normal baseline thresholds (AQI < 100, complaints < 15, Low/Medium traffic)."
        
        response += "\n\n*Recommendation*: Focus department resources on the top listed areas. Deployment of environmental monitors in these hotspots is highly suggested."
        return response

    # Intent B: Highest risk
    elif any(k in q_lower for k in ["highest risk", "max risk", "worst area", "most vulnerable"]):
        if not highest_risk_rec:
            return "No community records available to assess risk."
            
        traffic_desc = "high congestion" if highest_risk_rec.traffic.lower() == "high" else "moderate traffic"
        return (
            f"### ⚠️ Highest Risk Area: **{highest_risk_rec.area}**\n\n"
            f"According to multi-indicator prioritization, **{highest_risk_rec.area}** holds the highest vulnerability index. "
            "Key parameters:\n"
            f"- **Complaints**: {highest_risk_rec.complaints} reported issues\n"
            f"- **Air Quality (AQI)**: {highest_risk_rec.aqi} (Unhealthy)\n"
            f"- **Traffic**: {highest_risk_rec.traffic} density\n\n"
            f"**Proposed Actions**:\n"
            f"1. Reroute logistics vehicles to reduce {traffic_desc}.\n"
            f"2. Initiate green space planning to buffer the AQI impacts."
        )

    # Intent C: Summarize issues
    elif any(k in q_lower for k in ["summarize", "summary", "overview", "report"]):
        summary = (
            f"### 📋 Community Indicators Overview\n\n"
            f"Here is a summary of issues recorded across **{len(db_records)}** neighborhoods:\n\n"
            f"- **Total Wards Analyzed**: {len(db_records)}\n"
            f"- **Total Logged Complaints**: {total_complaints} across all areas\n"
            f"- **Average AQI**: {int(sum(r.aqi for r in db_records)/len(db_records))}\n\n"
            "**Key Findings**:\n"
        )
        
        findings = []
        if high_aqi_areas:
            findings.append(f"• **Air Quality issues** in: {', '.join(high_aqi_areas)}")
        if high_complaints_areas:
            findings.append(f"• **High volume of complaints** in: {', '.join(high_complaints_areas)}")
        if high_traffic_areas:
            findings.append(f"• **Gridlocks and traffic concerns** in: {', '.join(high_traffic_areas)}")
            
        if findings:
            summary += "\n".join(findings)
        else:
            summary += "• No severe indicator deviations detected. All wards are running smoothly."
            
        return summary

    # Intent D: Specific area query
    for r in db_records:
        if r.area.lower() in q_lower:
            status = "Unhealthy" if r.aqi > 100 else ("Moderate" if r.aqi > 50 else "Good")
            return (
                f"### 🏙️ Neighborhood Analysis: **{r.area}**\n\n"
                f"Metrics for **{r.area}**:\n"
                f"- **Complaints**: {r.complaints} open cases\n"
                f"- **Traffic Density**: {r.traffic}\n"
                f"- **Air Quality (AQI)**: {r.aqi} ({status})\n\n"
                f"*Assistant's Evaluation*: **{r.area}** is currently experiencing **{r.traffic.lower()}** traffic density and **{status.lower()}** air quality. "
                f"Policy recommendations focus on optimizing civic responses to address the {r.complaints} complaints."
            )

    # Default general chat
    return (
        f"### 🏙️ Community Decision Assistant\n\n"
        f"I am analyzing **{len(db_records)}** neighborhood records in AlloyDB. "
        "You can ask me questions about specific indicators or request summaries:\n"
        "- *Which ward needs attention?*\n"
        "- *What area has the highest risk?*\n"
        "- *Summarize community issues.*\n\n"
        f"Currently, your database has reports for: **{', '.join(r.area for r in db_records)}**."
    )


# ==========================================
# AI Insight Generation Engine
# ==========================================

INSIGHTS_SYSTEM_PROMPT = """You are an urban policy planner and community health analyst.
Analyze the following neighborhood metrics:
{data_context}

Generate a structured JSON array of community insights. Each element in the array MUST correspond to a specific neighborhood or be a "City-wide Summary".
You must formulate the output as a valid JSON array of objects. Do NOT output markdown code block wrappers (like ```json). Return ONLY the raw JSON string.

Each object must follow this schema:
{{
    "area": "Neighborhood Name or City-wide Summary",
    "insight": "Emerging trends, Community Health Score (assess score out of 100 based on AQI and complaints), and high-risk indicators description.",
    "priority_score": 8.2, (a floating point number between 0.0 and 10.0 indicating urgency)
    "recommendation": "Specific resource allocation suggestions and sustainability recommendations."
}}
"""

def generate_insights(db_records: List[Any]) -> List[Dict[str, Any]]:
    """
    Triggers Vertex AI Gemini to generate structured insights and recommendations
    based on community data. Falls back to local simulation if Vertex AI is not initialized.
    """
    if not db_records:
        return []

    if vertex_initialized and generative_model:
        try:
            import json
            data_context = format_db_context(db_records)
            prompt = INSIGHTS_SYSTEM_PROMPT.format(data_context=data_context)
            
            response = generative_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Sanitize potential markdown code block formatting
            if response_text.startswith("```"):
                # strip lead/trail markers
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()
                
            parsed_insights = json.loads(response_text)
            if isinstance(parsed_insights, list):
                # Ensure all elements have the expected schema keys
                validated_insights = []
                for item in parsed_insights:
                    if isinstance(item, dict) and "area" in item and "insight" in item:
                        validated_insights.append({
                            "area": str(item.get("area", "Unknown")),
                            "insight": str(item.get("insight", "")),
                            "priority_score": float(item.get("priority_score", 0.0)),
                            "recommendation": str(item.get("recommendation", ""))
                        })
                return validated_insights
        except Exception as e:
            logger.error(f"Failed to generate AI insights via Vertex AI: {str(e)}")
            # Fall back to simulation on error
            pass

    return simulate_generate_insights(db_records)

def simulate_generate_insights(db_records: List[Any]) -> List[Dict[str, Any]]:
    """
    Simulates Gemini's analysis by inspecting the database records and generating
    high-fidelity structural insights and policy recommendations.
    """
    if not db_records:
        return []
    
    insights = []
    
    # 1. Generate per-area insights
    for r in db_records:
        issues = []
        recommendations = []
        score = 0.0
        
        # AQI Assessment
        if r.aqi > 150:
            issues.append(f"Dangerous AQI level ({r.aqi})")
            recommendations.append("Limit diesel commercial vehicles, deploy local air filtration units, and declare emergency buffer protocols.")
            score += 4.5
        elif r.aqi > 100:
            issues.append(f"Unhealthy AQI level ({r.aqi}) for sensitive groups")
            recommendations.append("Establish low-emission school buffer zones and prioritize municipal tree plantings.")
            score += 2.5
        else:
            issues.append(f"Good/Moderate AQI level ({r.aqi})")
            recommendations.append("Expand urban cycling trails and maintain existing municipal tree reserves.")
            score += 0.5
            
        # Complaints Assessment
        if r.complaints > 20:
            issues.append(f"high infrastructure complaints volume ({r.complaints} active tickets)")
            recommendations.append("Direct immediate public works task forces to resolve local backlogs.")
            score += 3.5
        elif r.complaints > 10:
            issues.append(f"moderate complaints volume ({r.complaints} tickets)")
            recommendations.append("Optimize regional maintenance pipelines to address tickets within 14 days.")
            score += 1.5
        else:
            score += 0.2
            
        # Traffic Assessment
        if r.traffic.lower() == "high":
            issues.append("emerging traffic gridlocks trend")
            recommendations.append("Install intelligent signal controllers and allocate high-occupancy bus lanes.")
            score += 2.0
            
        # Calculate final priority score cap at 10.0
        priority_score = min(score, 10.0)
        
        # Calculate a health score for the community
        health_score = max(10, int(100 - (r.aqi * 0.3) - (r.complaints * 1.5)))
        
        insight_text = (
            f"Community Health Score: {health_score}/100. "
            f"Key findings indicate {', '.join(issues)}. "
            "Emerging trends warn of localized emissions concentrations."
        )
        
        rec_text = (
            f"Resource Allocation: {recommendations[0] if recommendations else 'Maintain standard patrol.'} "
            f"Sustainability Action: {recommendations[1] if len(recommendations) > 1 else 'Develop green spaces.'}"
        )
        
        insights.append({
            "area": r.area,
            "insight": insight_text,
            "priority_score": round(priority_score, 1),
            "recommendation": rec_text
        })
        
    # 2. Add a city-wide macro summary insight
    total_complaints = sum(r.complaints for r in db_records)
    avg_aqi = sum(r.aqi for r in db_records) / len(db_records)
    city_health_score = int(sum(max(10, 100 - (r.aqi * 0.3) - (r.complaints * 1.5)) for r in db_records) / len(db_records))
    
    insights.append({
        "area": "City-wide Summary",
        "insight": (
            f"Overall City Health Score: {city_health_score}/100. "
            f"Emerging trend: Aggregate complaints at {total_complaints} and average AQI at {int(avg_aqi)}. "
            "Micro-environmental hotspots continue to emerge near high-congestion transit corridors."
        ),
        "priority_score": 7.0,
        "recommendation": (
            "Resource Allocation: Prioritize capital projects fund toward wards exceeding 15 complaints or 100 AQI. "
            "Sustainability: Establish urban micro-forestry networks and enforce idle-free zones."
        )
    })
    
    return insights


# ==========================================
# AI Recommendations Generation Engine
# ==========================================

RECOMMENDATIONS_SYSTEM_PROMPT = """You are an expert city planner and public works director.
Analyze the following neighborhood metrics that have been sorted by their calculated risk score (higher score = more urgent risk):
{data_context}

For each neighborhood, generate:
1. "recommended_actions": Specific policy changes, transit adaptations, or safety warnings tailored to the complaints and air quality.
2. "resource_allocation": Specific municipal budgeting recommendations and physical resource allocation details (e.g. money, taskforces, air scrubbers).

Respond ONLY with a valid JSON array matching this structure. Do NOT include markdown code block wrappers (like ```json). Just the raw JSON.
Each object must have the keys: "area", "recommended_actions", and "resource_allocation".
"""

def generate_recommendations(records_with_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Query Gemini / Vertex AI to generate specific recommended actions and resource allocation
    suggestions for a list of neighborhoods with calculated risk scores.
    """
    if not records_with_scores:
        return []

    if vertex_initialized and generative_model:
        try:
            import json
            # Format input data
            context_lines = []
            for item in records_with_scores:
                context_lines.append(
                    f"Neighborhood: {item['area']}\n"
                    f" - Risk Score: {item['risk_score']:.1f}\n"
                    f" - Complaints: {item['complaints']}\n"
                    f" - Traffic: {item['traffic']}\n"
                    f" - AQI: {item['aqi']}\n"
                )
            data_context = "\n".join(context_lines)
            
            prompt = RECOMMENDATIONS_SYSTEM_PROMPT.format(data_context=data_context)
            
            response = generative_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Sanitize markdown formatting
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()
                
            parsed_recs = json.loads(response_text)
            if isinstance(parsed_recs, list):
                # Map generated recommendations back by neighborhood name
                rec_map = {}
                for item in parsed_recs:
                    if isinstance(item, dict) and "area" in item:
                        rec_map[item["area"].lower().strip()] = {
                            "recommended_actions": str(item.get("recommended_actions", "")),
                            "resource_allocation": str(item.get("resource_allocation", ""))
                        }
                        
                # Attach to our original list
                final_results = []
                for item in records_with_scores:
                    key = item["area"].lower().strip()
                    recs = rec_map.get(key, {
                        "recommended_actions": f"Review indicators (AQI: {item['aqi']}, Complaints: {item['complaints']}) and adjust local patrol.",
                        "resource_allocation": "Allocate baseline public safety and environmental surveillance budget."
                    })
                    final_results.append({
                        **item,
                        **recs
                    })
                return final_results
        except Exception as e:
            logger.error(f"Failed to generate recommendations via Vertex AI: {str(e)}")
            # Fall back to simulation on error
            pass

    return simulate_generate_recommendations(records_with_scores)

def simulate_generate_recommendations(records_with_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Local rule-based generator fallback producing structured recommendations based on risk metrics.
    """
    results = []
    for item in records_with_scores:
        area = item["area"]
        score = item["risk_score"]
        traffic = item["traffic"]
        complaints = item["complaints"]
        aqi = item["aqi"]
        
        actions = []
        resources = []
        
        # AQI Policy
        if aqi > 150:
            actions.append(f"Issue hazardous AQI alerts for {area} and distribute community filtration masks.")
            resources.append("Deploy $45,000 for emergency air scrubbers in city halls.")
        elif aqi > 100:
            actions.append(f"Establish low-emission zones near school districts in {area} to protect vulnerable citizens.")
            resources.append("Allocate $20,000 for localized air monitoring node deployments.")
        else:
            actions.append(f"Maintain local green space preservation in {area}.")
            resources.append("Allocate standard park maintenance grants.")
            
        # Traffic Policy
        if traffic.lower() == "high":
            actions.append("Design traffic rerouting schedules for logistics fleets to clear peak bottlenecks.")
            resources.append("Deploy 4 transit monitoring controllers and allocate $15,000 for signaling modifications.")
        elif traffic.lower() == "medium":
            actions.append("Optimize green-wave signal timings during commuter hours.")
            resources.append("Standard traffic control deployment.")
            
        # Complaints Policy
        if complaints > 20:
            actions.append(f"Dispatch emergency municipal repair crews to clean the {complaints} complaints backlog.")
            resources.append(f"Allocate $25,000 in civic repair work-orders to close all pending complaints within 7 days.")
        elif complaints > 10:
            actions.append("Accelerate utility checks to address tickets within standard 14-day turnaround.")
            resources.append("Direct standard maintenance patrols.")
            
        if not actions:
            actions.append(f"Perform baseline civic inspections and standard air checks for {area}.")
            resources.append("Maintain baseline operational budgeting.")
            
        results.append({
            **item,
            "recommended_actions": " ".join(actions),
            "resource_allocation": " ".join(resources)
        })
        
    return results


