import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Служба безопасности банка Хоббитон")
        self.configure(bg="black")
        
        # Button to go to the next day
        self.btn_next_day = ttk.Button(self, text="Перейти на день вперед", command=self.go_to_next_day)
        self.btn_next_day.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Label to show the current date
        self.lbl_current_date = tk.Label(self, text="Сегодняшняя дата - 13.05.2024", bg="black", fg="red", font=("Arial", 12))
        self.lbl_current_date.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        # Requests button
        self.btn_requests = tk.Button(self, text="Запросы", bg="red", fg="white", font=("Arial", 12), command=self.show_requests)
        self.btn_requests.grid(row=1, column=1, pady=20)
        
        # Charts button
        self.btn_charts = tk.Button(self, text="Графики", bg="red", fg="white", font=("Arial", 12), command=self.show_charts)
        self.btn_charts.grid(row=2, column=1, pady=20)
        
    def go_to_next_day(self):
        current_date = datetime.strptime(self.lbl_current_date.cget("text").split('- ')[1], "%d.%m.%Y")
        next_date = current_date + timedelta(days=1)
        self.lbl_current_date.config(text="Сегодняшняя дата - " + next_date.strftime("%d.%m.%Y"))
    
    def show_requests(self):
        print("Запросы")
        # Here you can add the code to handle the Requests button click event
    
    def show_charts(self):
        print("Графики")
        # Here you can add the code to handle the Charts button click event

if __name__ == "__main__":
    app = MainApp()
    app.geometry("500x400")
    app.mainloop()