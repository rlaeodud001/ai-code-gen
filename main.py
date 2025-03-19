import os

project_dir = "gemini-code-generator"
if not os.path.exists(project_dir):
    os.makedirs(project_dir)
    print(f"프로젝트 폴더 '{project_dir}'가 생성되었습니다.")
else:
    print(f"프로젝트 폴더 '{project_dir}'가 이미 존재합니다.")

main_py_path = os.path.join(project_dir, "main.py")
env_path = os.path.join(project_dir, ".env")
requirements_path = os.path.join(project_dir, "requirements.txt")

main_py_content = '''import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY가 환경 변수에 설정되어 있지 않습니다.")

genai.configure(api_key=api_key)

class CodeGenerator:
    def __init__(self):
        # 모델 설정 - Gemini Pro 모델 사용
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat_history = []
        
    def generate_code(self, prompt):
        """사용자의 프롬프트에 따라 코드를 생성합니다."""
        try:
            enhanced_prompt = f"""다음 요구사항에 맞는 코드를 생성해주세요:
            {prompt}
            
            코드를 생성할 때 다음 사항을 고려해주세요:
            1. 코드는 실행 가능하고 오류가 없어야 합니다.
            2. 필요한 주석을 포함하여 코드를 이해하기 쉽게 작성해주세요.
            3. 코드 블록은 마크다운 형식(```언어명)으로 감싸주세요.
            4. 코드에 대한 간단한 설명도 함께 제공해주세요.
            """
            
            response = self.model.generate_content(enhanced_prompt)
            self.chat_history = [{"role": "user", "parts": [prompt]}, 
                                {"role": "model", "parts": [response.text]}]
            return response.text
        except Exception as e:
            return f"코드 생성 중 오류가 발생했습니다: {str(e)}"
    
    def improve_code(self, code, feedback):
        """기존 코드를 사용자의 피드백에 따라 개선합니다."""
        try:
            improvement_prompt = f"""다음 코드를 개선해주세요:
            
            ```
            {code}
            ```
            
            개선 요청 사항:
            {feedback}
            
            개선된 코드를 제공하고, 변경 사항을 설명해주세요.
            """
            
            # 채팅 기록에 새로운 메시지 추가
            self.chat_history.append({"role": "user", "parts": [improvement_prompt]})
            
            # 채팅 세션 생성
            chat = self.model.start_chat(history=self.chat_history)
            response = chat.send_message(improvement_prompt)
            
            # 응답 저장
            self.chat_history.append({"role": "model", "parts": [response.text]})
            return response.text
        except Exception as e:
            return f"코드 개선 중 오류가 발생했습니다: {str(e)}"

def extract_code_block(text):
    """마크다운 형식의 코드 블록을 추출합니다."""
    if "```" in text:
        start = text.find("```") + 3
        # 언어 명시 부분 건너뛰기
        if "\\n" in text[start:]:
            start = text.find("\\n", start) + 1
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    return ""

def execute_code(code):
    """코드를 안전하게 실행하고 결과를 반환합니다."""
    # 임시 파일에 코드 저장
    temp_file = "temp_code.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(code)
    
    # 별도 프로세스에서 코드 실행
    import subprocess
    try:
        result = subprocess.run(["python", temp_file], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return f"실행 오류:\\n{result.stderr}"
        else:
            return f"실행 성공:\\n{result.stdout}"
    except subprocess.TimeoutExpired:
        return "실행 시간이 초과되었습니다."
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    print("=" * 50)
    print("제미나이 API 기반 코드 생성기")
    print("=" * 50)
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.")
    
    generator = CodeGenerator()
    current_code = ""
    
    while True:
        if not current_code:
            print("\\n새로운 코드를 생성합니다.")
            prompt = input("원하는 코드에 대해 설명해주세요: ")
            
            if prompt.lower() in ['exit', 'quit']:
                print("프로그램을 종료합니다.")
                break
                
            print("\\n코드 생성 중...")
            result = generator.generate_code(prompt)
            print("\\n생성된 코드:")
            print(result)
            
            # 코드 블록 추출 시도
            try:
                current_code = extract_code_block(result)
                if current_code:
                    print("\\n추출된 코드:")
                    print(current_code)
            except:
                current_code = result
        
        else:
            action = input("\\n다음 중 선택하세요:\\n1. 코드 실행\\n2. 코드 개선\\n3. 새 코드 생성\\n4. 종료\\n선택: ")
            
            if action == '1':
                try:
                    print("\\n코드 실행 결과:")
                    exec_result = execute_code(current_code)
                    print(exec_result)
                except Exception as e:
                    print(f"실행 중 오류 발생: {str(e)}")
                    feedback = input("코드를 개선하시겠습니까? (y/n): ")
                    if feedback.lower() == 'y':
                        improvement = input("어떻게 개선하면 좋을지 설명해주세요: ")
                        print("\\n코드 개선 중...")
                        improved_code = generator.improve_code(current_code, f"실행 중 다음 오류가 발생했습니다: {str(e)}. {improvement}")
                        print("\\n개선된 코드:")
                        print(improved_code)
                        try:
                            current_code = extract_code_block(improved_code)
                            if current_code:
                                print("\\n추출된 코드:")
                                print(current_code)
                        except:
                            current_code = improved_code
            
            elif action == '2':
                feedback = input("어떻게 코드를 개선하고 싶은지 설명해주세요: ")
                print("\\n코드 개선 중...")
                improved_code = generator.improve_code(current_code, feedback)
                print("\\n개선된 코드:")
                print(improved_code)
                try:
                    current_code = extract_code_block(improved_code)
                    if current_code:
                        print("\\n추출된 코드:")
                        print(current_code)
                except:
                    current_code = improved_code
            
            elif action == '3':
                current_code = ""
                continue
                
            elif action == '4':
                print("프로그램을 종료합니다.")
                break
                
            else:
                print("잘못된 선택입니다. 다시 시도해주세요.")

if __name__ == "__main__":
    main()
'''

env_content = '''
GEMINI_API_KEY=제미나이 api키
'''

requirements_content = '''google-generativeai>=0.3.0
python-dotenv>=1.0.0
'''

def create_file(path, content):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content.strip())
        print(f"파일 '{path}'가 생성되었습니다.")
    else:
        print(f"파일 '{path}'가 이미 존재합니다.")

create_file(main_py_path, main_py_content)
create_file(env_path, env_content)
create_file(requirements_path, requirements_content)

print("\n프로젝트 설정이 완료되었습니다!")
print(f"프로젝트 디렉토리: {os.path.abspath(project_dir)}")
print("\n다음 단계:")
print("1. .env 파일에 실제 제미나이 API 키를 설정하세요.")
print("2. 필요한 패키지를 설치하세요: pip install -r requirements.txt")
print("3. 프로그램을 실행하세요: python main.py")
