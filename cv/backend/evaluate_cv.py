import os
import uuid
import re
import fitz  # PyMuPDF
import google.generativeai as genai
import json
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cv_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = "AIzaSyD7Xqg9tpOaFZk11WSDoivTOBUmZG86gHE"

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# In-memory storage for analysis results
results_storage = {}

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.error("GEMINI_API_KEY not found")
    raise ValueError("GEMINI_API_KEY is required. Set it in .env file.")

def validate_pdf_file(file):
    """Validate uploaded PDF file."""
    if not file:
        logger.error("No file uploaded")
        raise ValueError("No file uploaded")
    if not file.filename.lower().endswith('.pdf'):
        logger.error(f"Invalid file format: {file.filename}")
        raise ValueError("Only PDF files are supported")
    return True

def extract_text_from_pdf(file):
    """Extract text from PDF file."""
    try:
        logger.info("Extracting text from uploaded PDF")
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if not text.strip():
            logger.warning("Extracted text is empty")
        logger.debug(f"Extracted PDF text: {text[:200]}...")
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF: {str(e)}")
        raise

def calculate_score(text, positive_keywords, negative_keywords, cv_text):
    """Calculate a score based on keyword presence, text length, and CV context."""
    score = 5  # Baseline
    text_lower = text.lower()
    cv_lower = cv_text.lower()
    
    for kw in positive_keywords:
        if kw in text_lower or kw in cv_lower:
            score += 1
            logger.debug(f"Positive keyword '{kw}' found, score +1")
    for kw in negative_keywords:
        if kw in text_lower or kw in cv_lower:
            score -= 1
            logger.debug(f"Negative keyword '{kw}' found, score -1")
    
    # Adjust for text detail
    if len(text) > 300:
        score += 1
        logger.debug("Text length > 300, score +1")
    elif len(text) < 100:
        score -= 1
        logger.debug("Text length < 100, score -1")
    
    # CV-specific adjustments
    if "gpa" in cv_lower or "chứng chỉ" in cv_lower:
        score += 1
        logger.debug("GPA or certification found in CV, score +1")
    if "dự án" in cv_lower and "kết quả" in text_lower:
        score += 1
        logger.debug("Project with results mentioned, score +1")
    
    return max(1, min(10, score))

def parse_text_response(text, cv_text):
    """Parse text-based CV analysis into JSON structure."""
    try:
        logger.info("Parsing text response into JSON")
        logger.debug(f"Raw response: {text[:500]}...")
        
        result = {
            "thong_tin_ca_nhan": {
                "diem": 5,
                "nhan_xet": "Thông tin cá nhân cơ bản, cần bổ sung chi tiết chuyên nghiệp hơn.",
                "de_xuat": "Thêm LinkedIn, sử dụng email chuyên nghiệp, loại bỏ biểu tượng."
            },
            "trinh_do_hoc_van": {
                "diem": 5,
                "nhan_xet": "Thông tin học vấn được trình bày, nhưng thiếu thành tích nổi bật.",
                "de_xuat": "Liệt kê GPA, chứng chỉ, hoặc dự án học tập để tăng sức thuyết phục."
            },
            "kinh_nghiem_lam_viec": {
                "diem": 5,
                "nhan_xet": "Kinh nghiệm làm việc sơ sài, cần mô tả chi tiết hơn.",
                "de_xuat": "Sử dụng động từ hành động, định lượng thành tựu (ví dụ: giảm 20% thời gian)."
            },
            "ky_nang": {
                "diem": 5,
                "nhan_xet": "Kỹ năng được liệt kê nhưng thiếu minh chứng cụ thể.",
                "de_xuat": "Cung cấp ví dụ sử dụng kỹ năng trong dự án hoặc công việc."
            },
            "du_an_portfolio": {
                "diem": 5,
                "nhan_xet": "Dự án được đề cập nhưng thiếu thông tin chi tiết.",
                "de_xuat": "Mô tả vai trò, kết quả, và cung cấp link portfolio hoặc GitHub."
            },
            "cau_truc_va_dinh_dang": {
                "diem": 5,
                "nhan_xet": "Cấu trúc CV cơ bản, cần cải thiện bố cục và tính thẩm mỹ.",
                "de_xuat": "Sử dụng font chữ thống nhất, tối ưu khoảng cách, và bố cục rõ ràng."
            },
            "ngon_ngu_va_cach_dien_dat": {
                "diem": 5,
                "nhan_xet": "Ngôn ngữ cần cải thiện về tính chuyên nghiệp và chính xác.",
                "de_xuat": "Kiểm tra kỹ chính tả, sử dụng từ ngữ chuyên ngành phù hợp."
            },
            "danh_gia_tong_the": {
                "diem_trung_binh": 5.0,
                "danh_gia_chi_tiet": "CV có tiềm năng nhưng cần cải thiện chi tiết, trình bày, và tính chuyên nghiệp để đáp ứng tiêu chuẩn tuyển dụng hiện đại.",
                "diem_manh": ["Có tiềm năng phát triển trong nhiều lĩnh vực khác nhau."],
                "diem_yeu": ["Thiếu chi tiết cụ thể.", "Trình bày chưa nổi bật."],
                "de_xuat_cai_thien": ["Thêm chi tiết về dự án và kỹ năng.", "Cải thiện bố cục CV.", "Kiểm tra chính tả kỹ lưỡng."],
                "nhan_xet_chung": "CV cần chỉnh sửa để tạo ấn tượng mạnh hơn với nhà tuyển dụng.",
                "tac_dong_thi_truong": "CV hiện tại chỉ đáp ứng được các yêu cầu cơ bản, cần cải thiện để cạnh tranh trong thị trường lao động."
            },
            "phan_tich_xu_huong": (
                "Xu hướng tuyển dụng hiện nay nhấn mạnh vào kỹ năng thực tế, "
                "khả năng sử dụng công cụ hiện đại, và kinh nghiệm dự án cụ thể. CV cần bổ sung chi tiết và chứng chỉ."
            )
        }

        # Define sections to extract
        sections = {
            "thong_tin_ca_nhan": r"1\. Thông tin cá nhân:(.*?)(?=(2\.|3\.|$))",
            "muc_tieu_nghe_nghiep": r"2\. Mục tiêu nghề nghiệp:(.*?)(?=(3\.|4\.|$))",
            "trinh_do_hoc_van": r"3\. Học vấn:(.*?)(?=(4\.|5\.|$))",
            "ky_nang": r"4\. Kỹ năng:(.*?)(?=(5\.|6\.|$))",
            "kinh_nghiem_lam_viec": r"5\. Kinh nghiệm và thành tích:(.*?)(?=(6\.|7\.|$))",
            "kien_thuc_diem_manh": r"6\. Kiến thức và điểm mạnh:(.*?)(?=(7\.|8\.|$))",
            "ngon_ngu_va_cach_dien_dat": r"7\. Ngôn ngữ:(.*?)(?=(8\.|$))",
            "so_thich": r"8\. Sở thích:(.*?)(?=(Tóm lại:|$))",
            "danh_gia_tong_the": r"Tóm lại:(.*?)$"
        }

        # Keyword-based scoring criteria
        scoring_criteria = {
            "thong_tin_ca_nhan": {
                "positive": ["đầy đủ", "rõ ràng", "chuyên nghiệp", "linkedin", "email", "địa chỉ"],
                "negative": ["thiếu", "không phù hợp", "icon", "biểu tượng", "kém chuyên nghiệp"]
            },
            "trinh_do_hoc_van": {
                "positive": ["gpa", "thành tích", "chứng chỉ", "rõ ràng", "liên quan"],
                "negative": ["thiếu", "không liên quan", "sơ sài"]
            },
            "kinh_nghiem_lam_viec": {
                "positive": ["dự án", "thành tựu", "định lượng", "github", "vai trò", "kết quả"],
                "negative": ["lặp lại", "thiếu chi tiết", "không thuyết phục", "sơ sài"]
            },
            "ky_nang": {
                "positive": ["phân loại", "cụ thể", "thành thạo", "trello", "figma", "sql", "excel"],
                "negative": ["chung chung", "thiếu chi tiết", "sơ sài"]
            },
            "du_an_portfolio": {
                "positive": ["dự án", "kết quả", "github", "vai trò", "portfolio"],
                "negative": ["lặp lại", "thiếu chi tiết", "sơ sài"]
            },
            "cau_truc_va_dinh_dang": {
                "positive": ["rõ ràng", "mạch lạc", "chuyên nghiệp", "dễ đọc"],
                "negative": ["dài dòng", "lặp lại", "khó hiểu", "sơ sài"]
            },
            "ngon_ngu_va_cach_dien_dat": {
                "positive": ["mạch lạc", "chuyên nghiệp", "ielts", "toeic", "chính xác"],
                "negative": ["lỗi chính tả", "chung chung", "sơ sài"]
            }
        }

        # Extract specific details from CV and response
        cv_lower = cv_text.lower()
        skills = re.findall(r"(trello|figma|draw\.io|sql|excel|python|java|javascript|swot)", cv_lower)
        projects = re.findall(r"(jewelry store management system|[^\s]+ project|[^\s]+ hệ thống)", cv_lower)
        certifications = re.findall(r"(ielts|toeic|google ai essentials|[^\s]+ certification|[^\s]+ chứng chỉ)", cv_lower)
        logger.debug(f"Extracted skills: {skills}, projects: {projects}, certifications: {certifications}")

        # Extract sections
        for key, pattern in sections.items():
            match = re.search(pattern, text, re.DOTALL)
            content = match.group(1).strip() if match else ""
            logger.debug(f"Extracted section '{key}': {content[:100]}...")
            
            if content:
                if key == "danh_gia_tong_the":
                    result[key]["danh_gia_chi_tiet"] = content
                    result[key]["nhan_xet_chung"] = content
                    result[key]["tac_dong_thi_truong"] = (
                        f"CV này có tiềm năng phát triển trong nhiều lĩnh vực, nhưng cần cải thiện chi tiết. "
                        "Để cạnh tranh tốt hơn, cần bổ sung chi tiết dự án, chứng chỉ, và cải thiện trình bày."
                    )
                elif key == "muc_tieu_nghe_nghiep":
                    result["cau_truc_va_dinh_dang"]["nhan_xet"] = content
                    result["cau_truc_va_dinh_dang"]["de_xuat"] = (
                        "Tóm tắt mục tiêu nghề nghiệp trong 2-3 câu, nhấn mạnh giá trị mang lại cho nhà tuyển dụng."
                    )
                    result["cau_truc_va_dinh_dang"]["diem"] = calculate_score(
                        content, ["chi tiết", "rõ ràng", "giá trị"], ["dài dòng", "chung chung"], cv_text
                    )
                elif key == "kien_thuc_diem_manh":
                    result["ky_nang"]["nhan_xet"] += f"\nKiến thức và điểm mạnh: {content}"
                    result["ky_nang"]["de_xuat"] += "\nTích hợp kiến thức vào kỹ năng, minh họa bằng ví dụ cụ thể."
                elif key == "so_thich":
                    result["danh_gia_tong_the"]["danh_gia_chi_tiet"] += f"\nSở thích: {content}"
                    result["danh_gia_tong_the"]["de_xuat_cai_thien"].append(
                        "Chọn sở thích thể hiện sự năng động và liên quan đến ngành nghề."
                    )
                else:
                    result[key]["nhan_xet"] = content
                    result[key]["de_xuat"] = f"Cải thiện chi tiết: {content[:200]}..."
                    if key in scoring_criteria:
                        result[key]["diem"] = calculate_score(
                            content,
                            scoring_criteria[key]["positive"],
                            scoring_criteria[key]["negative"],
                            cv_text
                        )
            else:
                logger.warning(f"No content extracted for section '{key}', using default")
                if key in scoring_criteria:
                    result[key]["diem"] = calculate_score(
                        result[key]["nhan_xet"],
                        scoring_criteria[key]["positive"],
                        scoring_criteria[key]["negative"],
                        cv_text
                    )

        # Enrich feedback based on CV content
        if skills:
            result["ky_nang"]["nhan_xet"] += f"\nKỹ năng đáng chú ý: {', '.join(skills).title()}."
            result["ky_nang"]["de_xuat"] += f"\nMô tả cách sử dụng {', '.join(skills)} trong dự án cụ thể."
            result["ky_nang"]["diem"] = min(10, result["ky_nang"]["diem"] + len(skills) // 2)
        if projects:
            result["du_an_portfolio"]["nhan_xet"] += f"\nDự án đáng chú ý: {', '.join(projects).title()}."
            result["du_an_portfolio"]["de_xuat"] += f"\nCung cấp chi tiết về {', '.join(projects)} (vai trò, kết quả, công nghệ)."
            result["du_an_portfolio"]["diem"] = min(10, result["du_an_portfolio"]["diem"] + len(projects))
        if certifications:
            result["trinh_do_hoc_van"]["nhan_xet"] += f"\nChứng chỉ đáng chú ý: {', '.join(certifications).title()}."
            result["trinh_do_hoc_van"]["de_xuat"] += f"\nNhấn mạnh {', '.join(certifications)} trong CV để tăng sức thuyết phục."
            result["trinh_do_hoc_van"]["diem"] = min(10, result["trinh_do_hoc_van"]["diem"] + len(certifications))

        # Populate job-related evaluation fields
        result["phan_tich_xu_huong"] = (
            f"Xu hướng tuyển dụng hiện nay trong các ngành nhấn mạnh vào kỹ năng thực tế, "
            f"khả năng sử dụng công cụ hiện đại, kinh nghiệm dự án cụ thể, và khả năng thích ứng. "
            f"CV cần bổ sung chi tiết, chứng chỉ và minh chứng kỹ năng để tăng sức cạnh tranh."
        )

        # Enrich danh_gia_tong_the
        result["danh_gia_tong_the"]["diem_manh"] = [
            f"Kỹ năng: {', '.join(skills).title()}" if skills else "Có tiềm năng phát triển kỹ năng.",
            f"Dự án: {', '.join(projects).title()}" if projects else "Có kinh nghiệm dự án cơ bản.",
            f"Chứng chỉ: {', '.join(certifications).title()}" if certifications else "Có nền tảng học vấn."
        ]
        result["danh_gia_tong_the"]["diem_yeu"] = [
            "Thiếu chi tiết trong mô tả dự án và kỹ năng." if not projects else "Cần định lượng kết quả dự án.",
            "Trình bày CV chưa tối ưu." if "dài dòng" in text.lower() else "Cần cải thiện bố cục CV.",
            "Chưa có chứng chỉ nổi bật." if not certifications else "Cần làm nổi bật chứng chỉ."
        ]
        result["danh_gia_tong_the"]["de_xuat_cai_thien"] = [
            "Thêm chi tiết cụ thể về dự án và kỹ năng.",
            "Cải thiện bố cục CV với font chữ và khoảng cách hợp lý.",
            "Kiểm tra chính tả và sử dụng từ ngữ chuyên ngành.",
            f"Làm nổi bật {', '.join(skills) if skills else 'kỹ năng kỹ thuật'} trong CV.",
            f"Cung cấp link portfolio cho {', '.join(projects) if projects else 'dự án'}."
        ]

        # Calculate average score
        scores = [result[key]["diem"] for key in result if key not in ["danh_gia_tong_the", "phan_tich_xu_huong"]]
        result["danh_gia_tong_the"]["diem_trung_binh"] = round(sum(scores) / len(scores), 1) if scores else 5.0
        logger.debug(f"Average score: {result['danh_gia_tong_the']['diem_trung_binh']}")

        # Validate output
        for key in result:
            if key not in ["danh_gia_tong_the", "phan_tich_xu_huong"] and not result[key]["nhan_xet"]:
                logger.warning(f"Empty nhan_xet for {key}, using default")
                result[key]["nhan_xet"] = f"Không có thông tin chi tiết cho {key.replace('_', ' ').title()}."
                result[key]["de_xuat"] = f"Cung cấp thêm thông tin về {key.replace('_', ' ').title()} để đánh giá chính xác hơn."
        logger.info("Parsing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error parsing text response: {str(e)}")
        return {"error": "Failed to parse text response", "raw_response": text}

def create_analysis_prompt(cv_text):
    """Create prompt for CV analysis across multiple industries."""
    return f"""
    Bạn là một chuyên gia đánh giá CV cao cấp với hơn 20 năm kinh nghiệm trong lĩnh vực tuyển dụng và phát triển nhân sự, AM HIỂU ĐA NGÀNH NGHỀ bao gồm công nghệ thông tin, tài chính - ngân hàng, giáo dục, kỹ thuật, y tế, marketing, quản lý, bán hàng, sản xuất và dịch vụ. Hãy phân tích CV sau đây một cách SÂU SẮC, CHI TIẾT, và CỤ THỂ, đánh giá theo các tiêu chí dưới đây. **Trả về kết quả dưới dạng JSON hợp lệ, tuân thủ cấu trúc được cung cấp. Không trả về văn bản thuần túy. Nếu CV thiếu thông tin, cung cấp đánh giá chi tiết với nhận xét cụ thể, điểm số hợp lý (4-6 cho nội dung cơ bản), và đề xuất cải thiện rõ ràng. Nếu không thể tạo JSON, trả về JSON với trường "error".**

    Các tiêu chí đánh giá (phân tích chi tiết cho từng tiêu chí, không chỉ một ngành nghề):
    1. Thông tin cá nhân: 
       - Đánh giá mức độ đầy đủ (tên, email, điện thoại, LinkedIn, GitHub, portfolio, website cá nhân)
       - Đánh giá tính chuyên nghiệp (email chuẩn ten.ho@gmail.com, không dùng biểu tượng không cần thiết)
       - Sự nổi bật (summary/profile statement gây ấn tượng, mục tiêu nghề nghiệp rõ ràng)
       - Phù hợp với từng ngành nghề (IT cần GitHub, Marketing cần portfolio, Tài chính cần chứng chỉ chuyên ngành)
       - Định dạng chuẩn mực (rõ ràng, dễ đọc, không quá rối mắt, thiết kế phù hợp với ngành)

    2. Trình độ học vấn: 
       - Chi tiết trình độ (trường, ngành học, GPA, thành tích học tập, học bổng, nghiên cứu)
       - Chứng chỉ chuyên môn phù hợp ngành nghề (IT: AWS, Microsoft; Marketing: Google Analytics; Tài chính: CFA, ACCA)
       - Các khóa học bổ sung/đào tạo ngắn hạn (nên nêu rõ kỹ năng đạt được sau khóa học)
       - Học vấn quốc tế (du học, trao đổi, thực tập nước ngoài - đặc biệt quan trọng cho ngành quốc tế)
       - Đánh giá sự liên quan của học vấn đến ngành nghề mong muốn (trường top, chuyên ngành phù hợp)

    3. Kinh nghiệm làm việc: 
       - Phân tích kỹ lưỡng mô tả công việc (có sử dụng động từ mạnh, kết quả rõ ràng, thành tựu định lượng)
       - Liên quan đến ngành nghề (đối với mỗi vị trí: phân tích kỹ năng chuyển đổi nếu chuyển ngành)
       - Tiến triển nghề nghiệp (thăng tiến rõ ràng, mức độ trách nhiệm tăng dần)
       - Đối với mỗi vị trí: quản lý dự án, quy mô đội nhóm, ngân sách, tác động kinh doanh cụ thể
       - Trình bày hợp lý (thông tin mới nhất trước, gọn gàng, dễ theo dõi, nhất quán)

    4. Kỹ năng: 
       - Phân tích kỹ lưỡng kỹ năng chuyên môn (phân loại theo ngành, mức độ thành thạo)
       - Đánh giá kỹ năng công nghệ/kỹ thuật/chuyên môn (theo từng ngành cụ thể)
       - Kỹ năng mềm và khả năng quản lý (làm việc nhóm, lãnh đạo, giao tiếp, quản lý thời gian)
       - Kỹ năng ngôn ngữ (trình độ cụ thể: IELTS, TOEIC, các ngôn ngữ khác)
       - Sự cân đối giữa kỹ năng cứng và mềm phù hợp vị trí (quản lý cần kỹ năng lãnh đạo, kỹ thuật cần chuyên môn sâu)

    5. Dự án/Portfolio: 
       - Đánh giá chi tiết dự án (mô tả, vai trò, kết quả, công nghệ sử dụng, quy mô, tác động)
       - Phân tích portfolio/sản phẩm cụ thể (đa dạng, chất lượng, sáng tạo)
       - URL hoặc link dẫn chứng (GitHub, Behance, portfolio cá nhân - đánh giá tính chuyên nghiệp)
       - Đóng góp nổi bật (sáng kiến, cải tiến, giải pháp mới)
       - Sự liên quan đến ngành nghề mong muốn (dự án nên phản ánh kỹ năng phù hợp với ngành)

    6. Cấu trúc và định dạng: 
       - Bố cục tổng thể (logic, nhất quán, dễ đọc, ấn tượng)
       - Thiết kế phù hợp ngành nghề (sáng tạo cho ngành thiết kế, chuyên nghiệp cho tài chính)
       - Độ dài phù hợp (1-2 trang cho sinh viên/nhân viên, 2-3 trang cho quản lý cấp cao)
       - Phông chữ và cỡ chữ (dễ đọc, thống nhất, chuyên nghiệp)
       - Định dạng nhấn mạnh (in đậm, sắp xếp hợp lý các thông tin quan trọng)

    7. Ngôn ngữ và cách diễn đạt: 
       - Đánh giá ngữ pháp và chính tả (không lỗi, chuyên nghiệp)
       - Phân tích từ ngữ chuyên ngành (sử dụng thuật ngữ đúng ngành nghề)
       - Sự ngắn gọn và súc tích (không dùng câu dài dòng, không lặp lại, tối ưu thông tin)
       - Cấu trúc câu và đoạn văn (rõ ràng, mạch lạc, nhấn mạnh thành tựu)
       - Sắc thái ngôn ngữ phù hợp (chuyên nghiệp, tích cực, chủ động, tự tin)

    **Cấu trúc JSON trả về (với phân tích CHI TIẾT, TOÀN DIỆN và THỰC TIỄN cho đa ngành nghề):**
    ```json
    {{
        "thong_tin_ca_nhan": {{
            "diem": 7, 
            "nhan_xet": "Phân tích chi tiết về thông tin cá nhân, đánh giá tính chuyên nghiệp của email, số điện thoại, và các thông tin liên hệ. Đánh giá sự phù hợp của summary statement với ngành nghề X, Y, Z. Nhận xét về cách trình bày và sự nổi bật của thông tin cá nhân. Đối với ngành X cần thông tin A, ngành Y cần thông tin B...", 
            "de_xuat": "Đề xuất cụ thể về cách cải thiện thông tin cá nhân: điều chỉnh email theo format chuyên nghiệp, thêm LinkedIn để tăng độ tin cậy, bổ sung resume statement ngắn gọn. Đối với ngành X nên bổ sung A, ngành Y nên bổ sung B..."
        }},
        "trinh_do_hoc_van": {{
            "diem": 8, 
            "nhan_xet": "Phân tích chi tiết trình độ học vấn, GPA, thành tích học tập. Đánh giá sự phù hợp của chuyên ngành với ngành nghề mục tiêu. Nhận xét về các chứng chỉ, khóa học bổ sung. Phân tích mức độ liên quan của học vấn đến các ngành X, Y, Z. Với ngành X, trình độ A là điểm mạnh, với ngành Y, trình độ B là điểm mạnh...", 
            "de_xuat": "Đề xuất cụ thể: nên nêu rõ thành tích học tập, thêm các dự án nghiên cứu, bổ sung chứng chỉ phù hợp ngành nghề. Đối với ngành X cần chứng chỉ A, ngành Y cần chứng chỉ B..."
        }},
        "kinh_nghiem_lam_viec": {{
            "diem": 6, 
            "nhan_xet": "Phân tích chi tiết kinh nghiệm làm việc, mức độ liên quan đến các ngành nghề mục tiêu. Đánh giá cách mô tả công việc, thành tựu, trách nhiệm. Nhận xét về việc sử dụng động từ mạnh, số liệu thành tựu. Phân tích kinh nghiệm phù hợp với ngành X, Y, Z. Với ngành X, kinh nghiệm A là quan trọng, với ngành Y, kinh nghiệm B là quan trọng...", 
            "de_xuat": "Đề xuất cụ thể: sử dụng động từ hành động mạnh mẽ, định lượng thành tựu (ví dụ: tăng doanh số 30%, giảm chi phí 25%). Đối với ngành X cần nhấn mạnh vai trò A, ngành Y cần làm rõ thành tựu B..."
        }},
        "ky_nang": {{
            "diem": 7, 
            "nhan_xet": "Phân tích chi tiết các kỹ năng chuyên môn và kỹ năng mềm. Đánh giá mức độ phù hợp với ngành nghề mục tiêu. Nhận xét về tính xác thực, minh chứng của kỹ năng. Phân tích kỹ năng phù hợp với ngành X, Y, Z. Với ngành X, kỹ năng A là thiết yếu, với ngành Y, kỹ năng B là quan trọng nhất...", 
            "de_xuat": "Đề xuất cụ thể: nên phân loại kỹ năng theo nhóm, chỉ rõ mức độ thành thạo, liên kết kỹ năng với kinh nghiệm thực tế. Đối với ngành X cần chứng minh kỹ năng A qua dự án cụ thể, ngành Y cần làm rõ khả năng sử dụng công cụ B..."
        }},
        "du_an_portfolio": {{
            "diem": 6, 
            "nhan_xet": "Phân tích chi tiết các dự án, vai trò, trách nhiệm, kết quả đạt được. Đánh giá tính liên quan và ấn tượng đối với nhà tuyển dụng. Nhận xét về cách trình bày portfolio. Phân tích dự án phù hợp với ngành X, Y, Z. Với ngành X, dự án A là nổi bật, với ngành Y, dự án B là quan trọng...", 
            "de_xuat": "Đề xuất cụ thể: mô tả rõ vai trò, trách nhiệm và kết quả đo lường được, thêm URL hoặc link GitHub, làm nổi bật đóng góp cá nhân. Đối với ngành X cần làm rõ tác động của dự án A, ngành Y cần nhấn mạnh quy mô của dự án B..."
        }},
        "cau_truc_va_dinh_dang": {{
            "diem": 6, 
            "nhan_xet": "Phân tích chi tiết cấu trúc CV, bố cục, trình bày. Đánh giá tính chuyên nghiệp, dễ đọc, thẩm mỹ. Nhận xét về sự phù hợp với ngành nghề. Phân tích định dạng phù hợp ngành X, Y, Z. Với ngành X, cấu trúc A là lý tưởng, với ngành Y, định dạng B là phù hợp nhất...", 
            "de_xuat": "Đề xuất cụ thể: cải thiện bố cục, sử dụng font chữ nhất quán, tối ưu khoảng trắng, nhấn mạnh thông tin quan trọng. Đối với ngành X nên sử dụng layout A, ngành Y nên sử dụng màu sắc và font B..."
        }},
        "ngon_ngu_va_cach_dien_dat": {{
            "diem": 5, 
            "nhan_xet": "Phân tích chi tiết về ngữ pháp, chính tả, cách diễn đạt. Đánh giá tính chuyên nghiệp, mạch lạc, súc tích. Nhận xét về việc sử dụng từ ngữ chuyên ngành. Phân tích ngôn ngữ phù hợp ngành X, Y, Z. Với ngành X, thuật ngữ A là cần thiết, với ngành Y, cách diễn đạt B là hiệu quả...", 
            "de_xuat": "Đề xuất cụ thể: kiểm tra lỗi chính tả kỹ lưỡng, sử dụng từ ngữ chuyên ngành chính xác, viết ngắn gọn và súc tích hơn. Đối với ngành X nên dùng thuật ngữ A, ngành Y nên nhấn mạnh kỹ năng giao tiếp B..."
        }},
        "danh_gia_tong_the": {{
            "diem_trung_binh": 6.5,
            "danh_gia_chi_tiet": "Đánh giá tổng thể chi tiết về CV, phân tích mức độ hoàn thiện, tính chuyên nghiệp, ấn tượng. Phân tích khả năng cạnh tranh trong thị trường lao động hiện tại. Nhận xét về CV đối với từng ngành nghề X, Y, Z. Với ngành X, CV có điểm mạnh A, với ngành Y, CV có điểm mạnh B...",
            "diem_manh": [
                "Điểm mạnh 1: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Điểm mạnh 2: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Điểm mạnh 3: Chi tiết, phân tích tác động đối với ngành X, Y, Z"
            ],
            "diem_yeu": [
                "Điểm yếu 1: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Điểm yếu 2: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Điểm yếu 3: Chi tiết, phân tích tác động đối với ngành X, Y, Z"
            ],
            "de_xuat_cai_thien": [
                "Đề xuất 1: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Đề xuất 2: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Đề xuất 3: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Đề xuất 4: Chi tiết, phân tích tác động đối với ngành X, Y, Z",
                "Đề xuất 5: Chi tiết, phân tích tác động đối với ngành X, Y, Z"
            ],
            "nhan_xet_chung": "Nhận xét chung chi tiết, tổng hợp tất cả các mặt của CV, đánh giá khả năng phù hợp với các ngành nghề X, Y, Z. Với ngành X, CV cần cải thiện A, với ngành Y, CV có thế mạnh B...",
            "tac_dong_thi_truong": "Phân tích chi tiết về khả năng cạnh tranh của CV trong thị trường lao động hiện tại đối với từng ngành nghề X, Y, Z. Đánh giá so với các ứng viên khác, xu hướng tuyển dụng, yêu cầu của nhà tuyển dụng. Với ngành X, CV đáp ứng A%, với ngành Y, CV đáp ứng B%..."
        }},
        "phan_tich_xu_huong": "Phân tích chi tiết về xu hướng tuyển dụng hiện tại đối với các ngành nghề phù hợp với CV. Đánh giá các kỹ năng đang được yêu cầu, sự cạnh tranh, cơ hội việc làm. Phân tích tác động của công nghệ, kinh tế, xã hội đến thị trường lao động trong các ngành phù hợp. Đối với ngành X, xu hướng A đang phát triển, ngành Y cần kỹ năng B..."
    }}
    ```

    Nội dung CV:
    {cv_text}

    **Lưu ý quan trọng**:
    - Phân tích TOÀN DIỆN theo hướng ĐA NGÀNH NGHỀ, không chỉ tập trung vào một ngành duy nhất như công nghệ thông tin.
    - Phân tích SÂU, CHI TIẾT, THỰC TIỄN, dựa trên nội dung thực tế của CV.
    - Đảm bảo tất cả các trường JSON được điền đầy đủ với nhận xét chi tiết (tối thiểu 100 từ mỗi nhận xét), điểm số hợp lý (1-10, dựa trên mức độ hoàn thiện), và đề xuất cụ thể.
    - Phân tích xu hướng thị trường lao động ĐA NGÀNH, đưa ra nhận định về nhu cầu thực tế của nhà tuyển dụng trong từng ngành phù hợp với ứng viên.
    - Nếu CV ngắn, vẫn cung cấp đánh giá chi tiết với điểm số 4-6, nhận xét về thiếu sót, và đề xuất cải thiện rõ ràng cho đa ngành nghề.
    """

def analyze_cv(cv_text):
    """Analyze CV using Gemini API with Gemini 1.5 Flash for faster response."""
    try:
        logger.info("Initializing Gemini 1.5 Flash API")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = create_analysis_prompt(cv_text)
        logger.info("Sending CV analysis request to Gemini 1.5 Flash API")
        response = model.generate_content(prompt)
        logger.debug(f"API response: {response.text[:500]}...")
        
        try:
            result = json.loads(response.text)
            logger.info("Successfully parsed JSON API response")
            return result
        except json.JSONDecodeError:
            logger.warning("API returned text instead of JSON, attempting to parse")
            return parse_text_response(response.text, cv_text)
    except Exception as e:
        logger.error(f"Error using Gemini API: {str(e)}")
        return {"error": f"Gemini API error: {str(e)}"}

@app.route('/upload', methods=['POST'])
def upload_cv():
    """Handle CV file upload and return analysis URL."""
    try:
        file = request.files.get('pdf')
        validate_pdf_file(file)
        
        logger.info(f"Processing uploaded file: {file.filename}")
        cv_text = extract_text_from_pdf(file)
        if not cv_text:
            logger.error("Failed to extract content from PDF")
            return jsonify({"error": "Failed to extract content from PDF"}), 400

        analysis = analyze_cv(cv_text)
        result_id = str(uuid.uuid4())
        
        results_storage[result_id] = {
            "analysis": analysis,
            "expires": datetime.now() + timedelta(hours=1)
        }
        
        result_url = url_for('get_results', result_id=result_id, _external=True)
        logger.info(f"Analysis completed, result URL: {result_url}")
        
        return jsonify({"result_url": result_url}), 200
    
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/results/<result_id>', methods=['GET'])
def get_results(result_id):
    """Return analysis results for a given result ID."""
    try:
        result = results_storage.get(result_id)
        if not result:
            logger.error(f"Result not found for ID: {result_id}")
            return jsonify({"error": "Result not found or expired"}), 404
        
        if datetime.now() > result["expires"]:
            logger.info(f"Result expired for ID: {result_id}")
            del results_storage[result_id]
            return jsonify({"error": "Result expired"}), 410
        
        logger.info(f"Returning results for ID: {result_id}")
        return jsonify({
            "raw": result["analysis"]
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}")
        return jsonify({"error": str(e)}), 500

def cleanup_expired_results():
    """Remove expired results from storage."""
    expired = [rid for rid, res in results_storage.items() if datetime.now() > res["expires"]]
    for rid in expired:
        logger.info(f"Cleaning up expired result: {rid}")
        del results_storage[rid]

if __name__ == "__main__":
    import threading
    import time
    
    def cleanup_task():
        while True:
            cleanup_expired_results()
            time.sleep(300)
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    
    logger.info("Starting Flask server on http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)