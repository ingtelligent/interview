from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import random
import datetime
import speech_recognition as sr
from flask_cors import CORS
import google.generativeai as genai
import re

app = Flask(__name__, static_folder='..', template_folder='..')
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for API endpoints

# Configure Gemini API
# Note: In a real application, use environment variables for the API key
GEMINI_API_KEY = "AIzaSyD7Xqg9tpOaFZk11WSDoivTOBUmZG86gHE"

# For demo purposes, we can disable Gemini and use random scoring if no API key is provided
USE_GEMINI = False
if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
    USE_GEMINI = True
    genai.configure(api_key=GEMINI_API_KEY)

# Load data
def load_data():
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    
    with open(os.path.join(data_path, 'data.json'), 'r', encoding='utf-8') as f:
        career_data = json.load(f)
    
    with open(os.path.join(data_path, 'model.json'), 'r', encoding='utf-8') as f:
        model_data = json.load(f)
    
    return career_data, model_data

# Global data
career_data, model_data = load_data()

# Session data (in a real app, you'd use a database)
sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('..', path)

@app.route('/api/careers', methods=['GET'])
def get_careers():
    """Return list of available careers"""
    careers = [{"id": career["id"], "name": career["name"]} for career in career_data["careers"]]
    return jsonify(careers)

@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    """Start a new interview session"""
    data = request.json
    name = data.get('name')
    age = data.get('age')
    job = data.get('job')
    
    if not name or not age or not job:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Find selected career
    selected_career = None
    for career in career_data["careers"]:
        if career["name"] == job:
            selected_career = career
            break
    
    if not selected_career:
        return jsonify({"error": "Invalid job selection"}), 400
    
    # Generate session ID
    session_id = f"session_{random.randint(10000, 99999)}_{int(datetime.datetime.now().timestamp())}"
    
    # Initialize session data
    sessions[session_id] = {
        "candidate": {
            "name": name,
            "age": age,
            "job": job
        },
        "career": selected_career,
        "current_criteria_index": 0,
        "current_question_index": 0,
        "results": []
    }
    
    # Initialize results structure
    for criteria in selected_career["criteria"]:
        sessions[session_id]["results"].append({
            "criteria_id": criteria["id"],
            "criteria_name": criteria["name"],
            "score": 0,
            "answer": ""
        })
    
    # Return first question
    return get_current_question(session_id)

def get_current_question(session_id):
    """Helper function to get the current question for a session"""
    if session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session = sessions[session_id]
    criteria_index = session["current_criteria_index"]
    question_index = session["current_question_index"]
    
    if criteria_index >= len(session["career"]["criteria"]):
        return jsonify({
            "complete": True,
            "session_id": session_id
        })
    
    current_criteria = session["career"]["criteria"][criteria_index]
    current_question = current_criteria["questions"][question_index]
    
    return jsonify({
        "session_id": session_id,
        "criteria": {
            "id": current_criteria["id"],
            "name": current_criteria["name"]
        },
        "question": current_question,
        "progress": {
            "criteria_index": criteria_index,
            "criteria_total": len(session["career"]["criteria"]),
            "question_index": question_index,
            "question_total": len(current_criteria["questions"])
        }
    })

def evaluate_answer_with_gemini(answer, criteria_name, question, job_position, levels):
    """Use Gemini to evaluate the answer against the given criteria levels"""
    if not USE_GEMINI:
        # Fallback to random scoring if Gemini is not configured
        return {
            "score": random.randint(1, 4),
            "reasoning": "Đánh giá tự động không khả dụng. Đây là đánh giá ngẫu nhiên."
        }
    
    try:
        # Create Gemini model instance
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Format the levels descriptions for the prompt
        levels_text = "\n".join([f"Level {level['score']}: {level['description']}" for level in levels])
        
        # Craft the prompt for evaluation
        prompt = f"""
        Bạn là chuyên gia đánh giá các buổi phỏng vấn. Hãy đánh giá câu trả lời dưới đây cho một câu hỏi phỏng vấn cho vị trí {job_position}.

        Tiêu chí đánh giá: {criteria_name}
        
        Câu hỏi: {question}
        
        Câu trả lời của ứng viên: {answer}
        
        Dựa trên các cấp độ đánh giá sau:
        {levels_text}
        
        Hãy đánh giá câu trả lời này thuộc cấp độ nào (1, 2, 3 hoặc 4) và giải thích lý do đánh giá.
        Trả lời theo định dạng:
        ĐÁNH GIÁ: [cấp độ - chỉ là con số từ 1-4]
        LÝ DO: [giải thích chi tiết]
        """
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        # Extract the score from the response using regex
        score_match = re.search(r'ĐÁNH GIÁ:\s*(\d+)', response.text, re.IGNORECASE)
        if score_match:
            score = int(score_match.group(1))
            # Ensure score is within valid range
            score = max(1, min(score, 4))
        else:
            # Default to middle score if we can't extract it
            score = 2
        
        # Extract reasoning
        reason_match = re.search(r'LÝ DO:\s*(.*?)(?=$|\n\n)', response.text, re.IGNORECASE | re.DOTALL)
        reason = reason_match.group(1).strip() if reason_match else "Không có giải thích cụ thể."
        
        return {
            "score": score,
            "reasoning": reason
        }
    except Exception as e:
        print(f"Error using Gemini API: {str(e)}")
        # Fallback to random scoring
        return {
            "score": random.randint(1, 4),
            "reasoning": "Đánh giá tự động không khả dụng. Đây là đánh giá ngẫu nhiên."
        }

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    """Submit an answer and get the next question"""
    data = request.json
    session_id = data.get('session_id')
    answer = data.get('answer')
    
    if not session_id or not answer:
        return jsonify({"error": "Missing required fields"}), 400
    
    if session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session = sessions[session_id]
    criteria_index = session["current_criteria_index"]
    question_index = session["current_question_index"]
    
    # Get current criteria and question
    current_criteria = session["career"]["criteria"][criteria_index]
    current_question = current_criteria["questions"][question_index]
    
    # Store answer
    session["results"][criteria_index]["answer"] += answer + "\n\n"
    
    # If this is the last question for this criteria, evaluate it
    if question_index == len(current_criteria["questions"]) - 1:
        # Get evaluation from Gemini API
        evaluation = evaluate_answer_with_gemini(
            answer=session["results"][criteria_index]["answer"],
            criteria_name=current_criteria["name"],
            question=current_question,
            job_position=session["candidate"]["job"],
            levels=current_criteria["levels"]
        )
        
        # Store the score and reasoning
        session["results"][criteria_index]["score"] = evaluation["score"]
        session["results"][criteria_index]["reasoning"] = evaluation["reasoning"]
    
    # Move to next question
    if question_index < len(current_criteria["questions"]) - 1:
        # Next question in the same criteria
        session["current_question_index"] += 1
    else:
        # Move to next criteria
        session["current_criteria_index"] += 1
        session["current_question_index"] = 0
    
    # Return next question
    return get_current_question(session_id)

@app.route('/api/finish-interview', methods=['POST'])
def finish_interview():
    """Finish the interview and return results"""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "Missing session ID"}), 400
    
    if session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session = sessions[session_id]
    
    # Calculate total score
    total_score = sum(result["score"] for result in session["results"])
    max_possible_score = len(session["career"]["criteria"]) * 4  # 4 is max score per criteria
    score_percentage = (total_score / max_possible_score) * 100
    
    # Generate overall evaluation
    try:
        if USE_GEMINI:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            results_text = ""
            for i, result in enumerate(session["results"]):
                results_text += f"{i+1}. {result['criteria_name']}: {result['score']}/4\n"
                if "reasoning" in result:
                    results_text += f"   Nhận xét: {result['reasoning']}\n\n"
            
            evaluation_prompt = f"""
            Hãy đưa ra đánh giá tổng quan cho ứng viên dựa trên kết quả phỏng vấn sau:
            
            Thông tin ứng viên:
            - Họ tên: {session['candidate']['name']}
            - Tuổi: {session['candidate']['age']}
            - Vị trí ứng tuyển: {session['candidate']['job']}
            
            Kết quả chi tiết:
            {results_text}
            
            Tổng điểm: {total_score}/{max_possible_score} ({score_percentage:.1f}%)
            
            Hãy viết một đánh giá tổng quan về ứng viên này, nêu rõ điểm mạnh, điểm yếu và đề xuất về khả năng phù hợp với vị trí. 
            Viết khoảng 3-5 đoạn văn một cách chuyên nghiệp, đưa ra những nhận xét có tính xây dựng.
            """
            
            response = model.generate_content(evaluation_prompt)
            evaluation = response.text.strip()
        else:
            # Fallback evaluation if Gemini is not configured
            raise Exception("Gemini API is not configured")
    except Exception as e:
        print(f"Error generating overall evaluation: {str(e)}")
        # Fallback evaluation if Gemini fails
        if score_percentage >= 80:
            evaluation = f"Ứng viên {session['candidate']['name']} thể hiện rất xuất sắc trong buổi phỏng vấn cho vị trí {session['candidate']['job']}. Ứng viên có kiến thức chuyên môn vững và kỹ năng tốt, phù hợp với yêu cầu của vị trí."
        elif score_percentage >= 60:
            evaluation = f"Ứng viên {session['candidate']['name']} thể hiện tốt trong buổi phỏng vấn cho vị trí {session['candidate']['job']}. Ứng viên có kiến thức cơ bản và kỹ năng cần thiết, nhưng cần phát triển thêm một số mặt."
        elif score_percentage >= 40:
            evaluation = f"Ứng viên {session['candidate']['name']} thể hiện ở mức trung bình trong buổi phỏng vấn cho vị trí {session['candidate']['job']}. Ứng viên cần cải thiện kiến thức và kỹ năng để đáp ứng yêu cầu công việc."
        else:
            evaluation = f"Ứng viên {session['candidate']['name']} chưa đáp ứng được yêu cầu cơ bản cho vị trí {session['candidate']['job']}. Ứng viên cần trau dồi thêm nhiều kiến thức và kỹ năng."
    
    # Return results
    results = {
        "candidate": session["candidate"],
        "total_score": total_score,
        "max_score": max_possible_score,
        "score_percentage": score_percentage,
        "evaluation": evaluation,
        "detailed_results": session["results"]
    }
    
    # Clean up session (or keep it for history in a real app)
    # del sessions[session_id]
    
    return jsonify(results)

@app.route('/api/listen', methods=['POST'])
def listen():
    """Endpoint to handle voice recognition"""
    # In a real implementation, you would handle audio streaming
    # This is a placeholder for the voice recognition functionality
    
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, timeout=5)
            text = r.recognize_google(audio, language='vi-VN')
            return jsonify({"success": True, "text": text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
