import tkinter as tk

judge_list = ['低体重（痩せすぎ）', '低体重（痩せ）', '低体重（痩せぎみ）', '普通体重',
              '肥満予備軍（過体重）', '肥満（1度）', '肥満（2度）', '肥満（3度）']


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # メインウィンドウの最小サイズを指定
        self.minsize(300, 200)
        # メインウィンドウの設定
        self.title("BMI計算機")
        # ウィジェット作成
        self.create_widgets()

    def create_widgets(self):

        # 3*5のグリッドを設定
        self.columnconfigure(index=0, weight=1)
        self.columnconfigure(index=1, weight=1)
        self.columnconfigure(index=2, weight=3)
        self.rowconfigure(index=0, weight=1)
        self.rowconfigure(index=1, weight=1)
        self.rowconfigure(index=2, weight=1)
        self.rowconfigure(index=3, weight=1)
        self.rowconfigure(index=4, weight=1)

        # ラベルの配置
        self.text_height = tk.StringVar()
        self.text_height.set("身長：")
        self.label = tk.Label(self.master, textvariable=self.text_height)
        self.label.grid(column=0, row=0, sticky='E')

        self.text_cm = tk.StringVar()
        self.text_cm.set('cm')
        self.label = tk.Label(self.master, textvariable=self.text_cm)
        self.label.grid(column=2, row=0, sticky='W')

        self.text = tk.StringVar()
        self.text.set("体重：")
        self.label = tk.Label(self.master, textvariable=self.text)
        self.label.grid(column=0, row=1, sticky='E')

        self.text_kg = tk.StringVar()
        self.text_kg.set('kg')
        self.label = tk.Label(self.master, textvariable=self.text_kg)
        self.label.grid(column=2, row=1, sticky='W')

        self.text_result = tk.StringVar()
        self.text_result.set('あなたのBMI指数は：')
        self.label = tk.Label(self.master, textvariable=self.text_result)
        self.label.grid(column=0, row=2, sticky='E')

        self.bmi_result = tk.StringVar()
        self.bmi_result.set('')
        self.label = tk.Label(self.master, textvariable=self.bmi_result)
        self.label.grid(column=1, row=2)

        self.text_judge = tk.StringVar()
        self.text_judge.set('判定は：')
        self.label = tk.Label(self.master, textvariable=self.text_judge)
        self.label.grid(column=0, row=3, sticky='E')

        self.judge = tk.StringVar()
        self.label = tk.Label(self.master, textvariable=self.judge)
        self.label.grid(column=1, row=3)

        # テキスト入力欄をメインウィンドウに配置
        # 身長入力欄
        self.enter_height = tk.DoubleVar()
        self.entry = tk.Entry(self.master, textvariable=self.enter_height, bg = 'white', justify="center", width=10)
        self.entry.grid(column=1, row=0)
        self.entry.delete(0, tk.END)

        # 体重入力欄
        self.enter_weight = tk.DoubleVar()
        self.entry = tk.Entry(self.master, textvariable=self.enter_weight, bg = 'white', justify="center", width=10)
        self.entry.grid(column=1, row=1)
        self.entry.delete(0, tk.END)

        # ボタンウィジェットをメインウィンドウに配置、イベントを登録
        self.button = tk.Button(self.master, text='計算する', bg = '#ffffff', activebackground = '#dddddd')
        self.button.bind("<Button-1>", self.bmi_cal)
        self.button.grid(column=1, row=4)

    # イベントハンドラ
    def bmi_cal(self, event):
        try:
            # BMI値を計算
            self.bmi_result.set('{:.3f}'.format(self.enter_weight.get() / (self.enter_height.get() / 100) ** 2))
            res = float(self.bmi_result.get())

            # BMI値によってカテゴリー判定を設定
            if res <= 0.0 or self.enter_height.get() <= 0:
                self.bmi_result.set("Error")
                self.judge.set("入力エラー")
            elif res < 16.0:
                self.judge.set(judge_list[0])
            elif res < 17.0:
                self.judge.set(judge_list[1])
            elif res < 18.5:
                self.judge.set(judge_list[2])
            elif res < 25.0:
                self.judge.set(judge_list[3])
            elif res < 30.0:
                self.judge.set(judge_list[4])
            elif res < 35.0:
                self.judge.set(judge_list[5])
            elif res < 40.0:
                self.judge.set(judge_list[6])
            else:
                self.judge.set(judge_list[7])

        except:
            self.bmi_result.set("Error")
            self.judge.set("入力エラー")


def main():
    root = App()
    root.mainloop()


if __name__ == "__main__":
    main()