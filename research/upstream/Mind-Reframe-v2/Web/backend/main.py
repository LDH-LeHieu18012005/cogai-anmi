# File: main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import httpx
from fastapi import HTTPException
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json

import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SessionInit(BaseModel):
    pass

class SessionData(BaseModel):
    session_id: str
    situation: str
    thought: str
    distortions: Optional[list] = None
    analysis: Optional[dict] = None
    candidates: Optional[list] = None
    selected_reframe: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

def clean_expired_sessions():
    """Remove sessions older than SESSION_EXPIRY_MINUTES"""
    now = datetime.now()
    expired = [
        sid for sid, data in sessions_store.items()
        if (now - data['updated_at']).seconds > SESSION_EXPIRY_MINUTES * 60
    ]
    for sid in expired:
        del sessions_store[sid]

def get_session(session_id: str) -> Optional[dict]:
    """Get session data by ID"""
    clean_expired_sessions()
    return sessions_store.get(session_id)

def update_session(session_id: str, data: dict):
    """Update session data"""
    if session_id in sessions_store:
        sessions_store[session_id].update(data)
        sessions_store[session_id]['updated_at'] = datetime.now()
    else:
        raise HTTPException(status_code=404, detail="Session not found")

class DetectionRequest(BaseModel):
    session_id: str
    situation: str
    thought: str

class AnalyzeRequest(BaseModel):
    session_id: str
    situation: str
    thought: str
    distortions: list

class ReframeRequest(BaseModel):
    session_id: str
    situation: str
    thought: str
    recommended_therapies: list

class FeedbackRequest(BaseModel):
    session_id: str
    situation: str
    thought: str
    current_reframe: str

class ImproveRequest(BaseModel):
    session_id: str
    situation: str
    thought: str
    current_reframe: str
    history_response: list
    feedback: str

API_base = 'http://localhost:1812/api/v1/'

sessions_store: Dict[str, dict] = {}

SESSION_EXPIRY_MINUTES = 60

class FeedbackData(BaseModel):
    session_id: str
    timestamp: str
    input: dict
    output: dict
    ratings: dict

@app.post("/api/feedback")
async def save_feedback(data: FeedbackData):
    try:
        # Chuyển đổi sang dict
        record = data.dict()
        
        # Ghi vào file dataset_feedback.jsonl
        # Mode 'a' (append) để ghi nối tiếp, không ghi đè
        with open("dataset_feedback.jsonl", "a", encoding="utf-8") as f:
            # Ghi mỗi feedback trên 1 dòng (JSONL format)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
        return {"status": "success", "message": "Feedback saved"}
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/session/init")
async def init_session():
    """Initialize a new session"""
    session_id = str(uuid.uuid4())
    sessions_store[session_id] = {
        'session_id': session_id,
        'situation': None,
        'thought': None,
        'distortions': None,
        'analysis': None,
        'candidates': None,
        'selected_reframe': None,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    return {"session_id": session_id}

def _check_has_distortion(text: str) -> bool:
    """Kiểm tra xem có distortion hay không"""
    if not text or len(text.strip()) < 10:
        return False
    
    # if '[' in text and ']' in text:
    #     return True
    
    positive_indicators = [
        "all-or-nothing", "mind reading", "catastrophizing",
        "overgeneralization", "mental filter", "labeling",
        "emotional reasoning", "should statements",
        "jumping to conclusions", "fortune telling",
        "personalization", "disqualifying"
    ]
    
    text_lower = text.lower()
    if any(indicator in text_lower for indicator in positive_indicators):
        return True
    
    negative_indicators = [
        "không có distortion", 
        "không phát hiện distortion",
        "no distortion",
        "không tìm thấy distortion"
    ]
    
    return not any(indicator in text_lower for indicator in negative_indicators)


def _extract_distortion_types(text: str) -> list:
    """
    Extract các loại distortion từ response
    Hỗ trợ format: [Type1, Type2, Type3] hoặc text tự do
    """
    import re
    
    bracket_match = re.search(r'\[(.*?)\]', text)
    if bracket_match:
        content = bracket_match.group(1)
        distortions = [d.strip() for d in content.split(',')]
        normalized = []
        for d in distortions:
            d_normalized = d.strip().title()
            if 'all-or-nothing' in d.lower():
                d_normalized = 'All-or-Nothing Thinking'
            elif 'mind reading' in d.lower():
                d_normalized = 'Mind Reading'
            elif 'catastrophizing' in d.lower():
                d_normalized = 'Catastrophizing'
            elif 'overgeneralization' in d.lower():
                d_normalized = 'Overgeneralization'
            elif 'mental filter' in d.lower():
                d_normalized = 'Mental Filter'
            elif 'jumping to conclusions' in d.lower():
                d_normalized = 'Jumping to Conclusions'
            elif 'fortune telling' in d.lower():
                d_normalized = 'Fortune Telling'
            elif 'emotional reasoning' in d.lower():
                d_normalized = 'Emotional Reasoning'
            elif 'should statements' in d.lower():
                d_normalized = 'Should Statements'
            elif 'labeling' in d.lower():
                d_normalized = 'Labeling'
            elif 'personalization' in d.lower():
                d_normalized = 'Personalization'
            elif 'disqualifying the positive' in d.lower():
                d_normalized = 'Disqualifying the Positive'
            elif 'magnification' in d.lower():
                d_normalized = 'Magnification'
            elif 'minimization' in d.lower():
                d_normalized = 'Minimization'
            elif 'blame' in d.lower():
                d_normalized = 'Blame'
            
            normalized.append(d_normalized)
        
        return normalized if normalized else ["Unknown Distortion"]
    
    common_distortions = {
        "all-or-nothing": "All-or-Nothing Thinking",
        "overgeneralization": "Overgeneralization",
        "mental filter": "Mental Filter",
        "disqualifying the positive": "Disqualifying the Positive",
        "jumping to conclusions": "Jumping to Conclusions",
        "mind reading": "Mind Reading",
        "fortune telling": "Fortune Telling",
        "magnification": "Magnification",
        "catastrophizing": "Catastrophizing",
        "minimization": "Minimization",
        "emotional reasoning": "Emotional Reasoning",
        "should statements": "Should Statements",
        "labeling": "Labeling",
        "personalization": "Personalization",
        "blame": "Blame"
    }
    
    found_distortions = []
    text_lower = text.lower()
    
    for key, distortion_name in common_distortions.items():
        if key in text_lower:
            found_distortions.append(distortion_name)
    
    seen = set()
    unique_distortions = []
    for d in found_distortions:
        if d not in seen:
            seen.add(d)
            unique_distortions.append(d)
    
    return unique_distortions if unique_distortions else ["Unknown Distortion"]


def _extract_explanation(text: str) -> str:
    """
    Extract phần giải thích từ response
    Bỏ qua phần danh sách distortions trong []
    """
    import re
    
    text_cleaned = re.sub(r'^\s*\[.*?\]\s*', '', text).strip()
    
    if text_cleaned:
        explanation = text_cleaned.strip()
        
        prefixes_to_remove = [
            "explanation:",
            "giải thích:",
            "phân tích:"
            # "the speaker"
        ]
        
        explanation_lower = explanation.lower()
        for prefix in prefixes_to_remove:
            if explanation_lower.startswith(prefix):
                explanation = explanation[len(prefix):].strip()
                if explanation:
                    explanation = explanation[0].upper() + explanation[1:]
                break
        
        return explanation
    
    return text.strip()

@app.post("/api/detect")
async def detect_distortion(request: DetectionRequest):
    try:
        update_session(request.session_id, {
            'situation': request.situation,
            'thought': request.thought
        })
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            dot_analysis = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": "dot.analysis", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            dot_analysis.raise_for_status()  
            result_analysis = dot_analysis.json()  
            analysis_response = result_analysis.get("result", "") or result_analysis.get("content", "")  # Fix: đổi result thành result_analysis

            # Bước 2: Gọi dot.detection với kết quả từ dot.analysis
            dot_detection = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": "dot.detection", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought,
                        "dot_analysis": analysis_response
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            
            dot_detection.raise_for_status()
            result_detection = dot_detection.json()  # Fix: đổi tên biến để rõ ràng
            
            ai_response = result_detection.get("result", "") or result_detection.get("content", "")  # Fix: dùng result_detection
            
            has_distortion = _check_has_distortion(ai_response)
            distortion_types = _extract_distortion_types(ai_response)
            explanation = _extract_explanation(ai_response)

            update_session(request.session_id, {
                'distortions': distortion_types if distortion_types else []
            })
            
            return {
                "session_id": request.session_id,
                "has_distortion": has_distortion,
                "distortion_types": distortion_types,
                "explanation": explanation,
                "raw_response": ai_response  
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi gọi API phân tích: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi không xác định: {str(e)}"
        )

def _parse_json_response(text: str) -> dict:
    """Parse JSON từ AI response, xử lý markdown và whitespace"""
    import json
    import re
    
    try:
        # Clean text
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # Parse JSON
        return json.loads(text)
        
    except json.JSONDecodeError as e:
        # Fallback: try to extract JSON from text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        raise ValueError(f"Không thể parse JSON response: {e}\nText: {text[:200]}")

@app.post("/api/analyze")
async def analyze_thought(request: AnalyzeRequest):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            thera_rcm = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": "dot.thera_rcm", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought, 
                        "distortions_type": request.distortions
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            thera_rcm.raise_for_status()  
            result = thera_rcm.json()
            print(request.situation)
            print(request.thought)
            print(request.distortions)
            
            ai_text = result.get("result", "") or result.get("content", "")
            parsed_result = _parse_json_response(ai_text)
            
            # Validate và add defaults nếu thiếu fields
            if "emotional_impact" not in parsed_result:
                parsed_result["emotional_impact"] = "Tác động cảm xúc đáng kể"
            
            if "underlying_beliefs" not in parsed_result or not parsed_result["underlying_beliefs"]:
                parsed_result["underlying_beliefs"] = ["Niềm tin cốt lõi cần được khám phá thêm"]
            
            if "triggers" not in parsed_result or not parsed_result["triggers"]:
                parsed_result["triggers"] = ["Các tình huống tương tự"]
            
            if "recommended_therapies" not in parsed_result or not parsed_result["recommended_therapies"]:
                # Default therapies based on common distortions
                parsed_result["recommended_therapies"] = ["CBT", "ACT"]
            parsed_result["session_id"] = request.session_id
            return parsed_result
        
    except json.JSONDecodeError as e:
        # Fallback response nếu parse JSON thất bại
        return {
            "session_id": request.session_id,
            "emotional_impact": "Lo âu và căng thẳng đáng kể do các suy nghĩ tiêu cực",
            "underlying_beliefs": [
                "Tôi cần được chấp nhận bởi người khác",
                "Tôi phải tránh thất bại bằng mọi giá",
                "Nếu có vấn đề xảy ra, đó là lỗi của tôi"
            ],
            "triggers": [
                "Tình huống liên quan đến mối quan hệ",
                "Áp lực và kỳ vọng",
                "Sự không chắc chắn"
            ],
            "recommended_therapies": ["CBT", "ACT", "DBT"]
        }
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi gọi API phân tích: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi không xác định: {str(e)}"
        )

# @app.post("/api/reframe")
# async def generate_reframe(request: ReframeRequest):
#     reframe_candidates = []
#     for therapy in request.recommended_therapies:
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.post(
#                     f"{API_base}prompts/templates/execute",
#                     json={
#                         "provider": "groq",
#                         "template_name": f"reframe.{therapy.lower()}", 
#                         "model": "openai/gpt-oss-20b",
#                         "variables": {
#                             "situation": request.situation,
#                             "thought": request.thought, 
#                         }
#                     },
#                     headers={
#                         "accept": "application/json",
#                         "Content-Type": "application/json"
#                     }
#                 )
#             response.raise_for_status()  
#             result = response.json()
            
#             reframe = result.get("reframing response", "")
#             # parsed_result = _parse_json_response(ai_text)
#             reframe_candidates.append({
#                 "therapy": f"{therapy}",
#                 "reframe": f"{reframe}",
#                 "rationale": "demo",
#                 "evaluation": {"empathy": 5, "logic": 4, "helpfulness": 5}
#             })
#     return reframe_candidates

@app.post("/api/reframe")
async def generate_reframe(request: ReframeRequest):
    async def fetch_reframe(therapy: str) -> Dict[str, Any]:
        """Fetch reframe for a single therapy type"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": f"reframe.{therapy.lower()}", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought, 
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()  
            result = response.json()
            
            # Parse JSON string trong trường 'content'
            import json
            content_str = result.get("content", "{}")
            content_json = json.loads(content_str)
            
            # Thử cả 2 key có thể có
            reframe = content_json.get("reframing response") or content_json.get("reframing_response", "")
            wtw = content_json.get("why_this_works") or content_json.get("why this works", "")

            feedback = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": f"dot.thera_supervisor", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought, 
                        "reframe_response": reframe
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            feedback.raise_for_status()  
            feedback = feedback.json()
            print(feedback)
            feedback_str = feedback.get("content", "{}")
            feedback_json = json.loads(feedback_str)
            return {
                "therapy": therapy,
                "reframe": reframe,
                "rationale": wtw,
                "evaluation": feedback_json
            }
    
    reframe_candidates = await asyncio.gather(
        *[fetch_reframe(therapy) for therapy in request.recommended_therapies],
        return_exceptions=True
    )
    successful_results = [
        result for result in reframe_candidates 
        if not isinstance(result, Exception)
    ]
    return {
        "session_id": request.session_id,
        "candidates": successful_results
    }

@app.post("/api/instruction_feedback")
async def generate_instruction_feedback(request: FeedbackRequest):
    try:   
        async with httpx.AsyncClient(timeout=30.0) as client:
            ai_feedback = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": "reframe.thera_supervisor_full", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought, 
                        "reframe_response": request.current_reframe
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            ai_feedback.raise_for_status()  
            ai_feedback = ai_feedback.json()  
            ai_feedback = ai_feedback.get("result", "") or ai_feedback.get("content", "")

            
            return {
                "session_id": request.session_id,
                "ai_feedback": ai_feedback,
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi gọi API phân tích: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi không xác định: {str(e)}"
        )

@app.post("/api/improve")
async def generate_improve_reframe(request: ImproveRequest):
    try:   
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": "reframe.cbtwfeedback", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought, 
                        "history_response": request.history_response, 
                        "old_response": request.current_reframe,
                        "feedback": request.feedback
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            response.raise_for_status()  
            result = response.json()
            import json
            content_str = result.get("content", "{}")
            content_json = json.loads(content_str)
        
            reframe = content_json.get("reframing response") or content_json.get("reframing_response", "")

            ai_feedback = await client.post(
                f"{API_base}prompts/templates/execute",
                json={
                    "provider": "openai",
                    "template_name": "reframe.thera_supervisor_full", 
                    "model": "gpt-4.1",
                    "variables": {
                        "situation": request.situation,
                        "thought": request.thought, 
                        "reframe_response": reframe
                    }
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            ai_feedback.raise_for_status()  
            ai_feedback = ai_feedback.json()  
            ai_feedback = ai_feedback.get("result", "") or ai_feedback.get("content", "")

            
            return {
                "session_id": request.session_id,
                "new_reframe": reframe,
                "ai_feedback": ai_feedback
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi gọi API phân tích: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi không xác định: {str(e)}"
        )

@app.post("/api/save")
async def save_selection(data: dict):
    print(f"User saved reframe: {data}")
    return {"status": "success"}


app.mount("/assets", StaticFiles(directory="../mind-reframe/dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path.startswith("api/"):
        return {"error": "Not Found"}
    
    return FileResponse("../mind-reframe/dist/index.html")