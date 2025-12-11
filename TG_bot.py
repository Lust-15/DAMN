from telegram.ext import Application
import os
def main():
    token ="token"
    app = Application.builder().token(token).build()
    print("Start")
    app.run_polling()


if __name__ == '__main__':
    main()