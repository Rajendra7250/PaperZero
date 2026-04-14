# ECO_FLOW — PaperZero

> A college paper-reduction ERP system that digitizes academic workflows, reducing dependency on physical paperwork across departments.

Built as a team project at **Hack Fusion**, KLS VDIT Haliyal.

---

## Features

- Role-based access for Students, Teachers, and Management
- Digital document submission and approval workflows
- Analytics dashboard for tracking paper usage reduction
- Secure authentication with session management
- Modular Flask Blueprint architecture

---

## Tech Stack

| Layer    | Technology                                      |
|----------|-------------------------------------------------|
| Backend  | Python, Flask, Flask-SQLAlchemy, Flask-Login    |
| Frontend | HTML, CSS, JavaScript                           |
| Auth     | Werkzeug, Flask-Login                           |
| Config   | python-dotenv                                   |

---

## Project Structure

```
PaperZero/
├── app.py              # Application entry point
├── run.py              # Runner script
├── config.py           # App configuration
├── models.py           # Database models
├── auth.py             # Authentication logic
├── Analytics.py        # Analytics module
├── Documents.py        # Document handling
├── templates/          # HTML templates
├── static/             # CSS, JS, assets
└── requirements.txt
```

---

## Getting Started

**1. Clone the repository**
```bash
git clone https://github.com/Rajendra7250/PaperZero.git
cd PaperZero
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment**

Create a `.env` file in the root directory:
```
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///paperzero.db
```

**4. Run the app**
```bash
python run.py
```

Open `http://localhost:5000` in your browser.

---

## Team

Built at **Hack Fusion** — KLS VDIT Haliyal

- [Rajendra Madiival](https://github.com/Rajendra7250)
- [Nikhil Hatti ](https://github.com/Rajendra7250)
- [Mukesh Ghanchi](https://github.com/Rajendra7250)
- [Saiprasad Ekabote](https://github.com/Rajendra7250)

---

## License

This project is open source and available under the [MIT License](LICENSE).
