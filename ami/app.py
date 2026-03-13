from ami.controllers.contact_controller import ContactController
from ami.controllers.note_controller import NoteController
from ami.database import init_db
from ami.views.main_window import MainWindow


def main():
    session = init_db()
    contact_ctrl = ContactController(session)
    note_ctrl = NoteController(session)
    app = MainWindow(contact_ctrl, note_ctrl)
    app.protocol("WM_DELETE_WINDOW", lambda: (session.close(), app.destroy()))
    app.mainloop()


if __name__ == "__main__":
    main()
