import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import sqlite3
import numpy as np

# 얼굴 인식 캐스케이드 파일 읽기
cascade_path = 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print(f"Error loading cascade file. Please ensure the file is in the correct path: {cascade_path}")
    exit()

# 데이터베이스 연결 (없으면 생성)
conn = sqlite3.connect('face_database.db')
c = conn.cursor()

# 테이블 생성
c.execute('''CREATE TABLE IF NOT EXISTS faces
             (id INTEGER PRIMARY KEY, name TEXT, image BLOB)''')

# Tkinter 메인 윈도우 생성
root = tk.Tk()
root.title("얼굴 등록 및 관리 시스템")
root.geometry("150x150")

# 색상 설정
bg_color = "#34495E"
fg_color = "#ECF0F1"
btn_color = "#1ABC9C"
entry_color = "#2C3E50"

# 스타일 설정
style = {
    "bg": bg_color,
    "fg": fg_color,
    "font": ("Helvetica", 12)
}

btn_style = {
    "bg": btn_color,
    "fg": fg_color,
    "font": ("Helvetica", 12),
    "padx": 10,
    "pady": 5,
    "relief": tk.RAISED,
    "bd": 3
}

entry_style = {
    "bg": entry_color,
    "fg": fg_color,
    "font": ("Helvetica", 12),
    "relief": tk.FLAT,
    "bd": 5,
    "insertbackground": fg_color
}

# 메인 프레임 설정
main_frame = tk.Frame(root, bg=bg_color)
main_frame.pack(fill=tk.BOTH, expand=True)

# 얼굴 등록 함수
def register_face():
    def submit_registration():
        file_path = filedialog.askopenfilename()
        if file_path:
            name = name_entry.get()
            if not name:
                messagebox.showerror("오류", "이름을 입력하세요")
                return

            img = cv2.imread(file_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                messagebox.showerror("오류", "얼굴을 감지하지 못했습니다.")
                return

            for (x, y, w, h) in faces:
                face_img = img[y:y+h, x:x+w]
                face_img = cv2.resize(face_img, (200, 200))
                _, face_img_encoded = cv2.imencode('.jpg', face_img)
                face_img_bytes = face_img_encoded.tobytes()

                # 얼굴 데이터를 데이터베이스에 삽입
                c.execute("INSERT INTO faces (name, image) VALUES (?, ?)", (name, face_img_bytes))
                conn.commit()

                img_pil = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
                img_tk = ImageTk.PhotoImage(img_pil)
                image_label.config(image=img_tk)
                image_label.image = img_tk

                messagebox.showinfo("성공", "얼굴 등록이 완료되었습니다.")
                break

    register_window = tk.Toplevel(root)
    register_window.title("얼굴 등록")
    register_window.configure(bg=bg_color)
    
    name_label = tk.Label(register_window, text="이름:", **style)
    name_label.pack(pady=(20, 5))
    name_entry = tk.Entry(register_window, **entry_style)
    name_entry.pack(pady=(0, 20))

    upload_btn = tk.Button(register_window, text="얼굴 이미지 업로드", command=submit_registration, **btn_style)
    upload_btn.pack()

    image_label = tk.Label(register_window, bg=bg_color)
    image_label.pack(pady=(20, 10))

# 얼굴 관리 함수
def manage_faces():
    def delete_face(face_id):
        response = messagebox.askyesno("삭제 확인", "정말로 이 얼굴을 삭제하시겠습니까?")
        if response:
            c.execute("DELETE FROM faces WHERE id = ?", (face_id,))
            conn.commit()
            messagebox.showinfo("성공", "얼굴이 삭제되었습니다.")
            manage_window.destroy()
            manage_faces()

    manage_window = tk.Toplevel(root)
    manage_window.title("얼굴 관리")
    manage_window.configure(bg=bg_color)

    c.execute("SELECT * FROM faces")
    rows = c.fetchall()

    for i, row in enumerate(rows):
        face_id, name, face_img_bytes = row
        face_img = cv2.imdecode(np.frombuffer(face_img_bytes, np.uint8), cv2.IMREAD_COLOR)
        face_img_pil = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        face_img_tk = ImageTk.PhotoImage(face_img_pil)

        label = tk.Label(manage_window, text=name, **style)
        label.grid(row=i, column=0, padx=10, pady=10)
        img_label = tk.Label(manage_window, image=face_img_tk, bg=bg_color)
        img_label.image = face_img_tk
        img_label.grid(row=i, column=1, padx=10, pady=10)
        delete_btn = tk.Button(manage_window, text="삭제", command=lambda face_id=face_id: delete_face(face_id), **btn_style)
        delete_btn.grid(row=i, column=2, padx=10, pady=10)

# 얼굴 등록 버튼 설정
register_btn = tk.Button(main_frame, text="얼굴 등록", command=register_face, **btn_style)
register_btn.pack(pady=20)

# 얼굴 관리 버튼 설정
manage_btn = tk.Button(main_frame, text="얼굴 관리", command=manage_faces, **btn_style)
manage_btn.pack(pady=20)

# Tkinter 메인 윈도우 실행
root.mainloop()

# 데이터베이스 연결 닫기
conn.close()
