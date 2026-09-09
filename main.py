import tkinter as tk
from gui import AutoExamGUI


def main():

    root = tk.Tk()

    root.title("Auto Exam Grader")
    root.geometry("800x600")
    root.resizable(False, False)

    app = AutoExamGUI(root)

    root.mainloop()


if __name__ == "__main__":
    main()