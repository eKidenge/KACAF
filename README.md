# KACAF

**Kenya Association of Community Action Facilitators (MIS)**

A web-based **Management Information System** built with **Django** to support governance, membership, programs, finance, events, and communications for the Kenya Association of Community Action Facilitators (KACAF).

---

## Overview

KACAF MIS is designed to digitize and streamline organizational operations through a modular, scalable, and secure web platform.
The system provides role-based access, centralized data management, and transparent reporting suitable for NGOs and community-based organizations.

---

## Objectives

- Digitize governance and administrative processes
- Manage members, programs, and projects efficiently
- Improve transparency in financial reporting
- Enhance internal and external communication
- Provide role-based dashboards for stakeholders

---

## Project Structure

templates/

├── base/

│   ├── base.html

│   ├── header.html

│   ├── footer.html

│   ├── sidebar.html

│   ├── navigation.html

│   └── messages.html

├── accounts/

│   ├── auth/

│   ├── user/

│   └── admin/

├── governance/

│   ├── assembly/

│   ├── resolution/

│   └── membership/

├── programs/

│   ├── program/

│   ├── project/

│   └── training/

├── finance/

│   ├── report/

│   ├── income/

│   └── expense/

├── events/

│   ├── event/

│   └── registration/

├── documents/

│   ├── document/

│   └── category/

├── communications/

│   ├── announcement/

│   └── contact/

└── dashboard/

├── admin_dashboard.html

├── executive_dashboard.html

├── member_dashboard.html

└── public_dashboard.html


---
##  Core Modules

###  Accounts & Authentication
- User registration and login
- Role-based access control
- Admin user management

### 🏛️ Governance
- General assemblies
- Resolutions tracking
- Membership applications

### 📊 Programs & Projects
- Program management
- Project tracking
- Training sessions

###  Finance
- Income and expense tracking
- Budget and financial reports

###  Events
- Event listing and details
- Event registration and calendar

###  Documents
- Document repository
- Categorized document management

###  Communications
- Announcements
- Contact and feedback forms

###  Dashboards
- Admin dashboard
- Executive dashboard
- Member dashboard
- Public dashboard
---
## Technology Stack

- **Backend:** Django (Python)
- **Frontend:** Django Templates (HTML, CSS, JS)
- **Database:** SQLite (development) / PostgreSQL (production-ready)
- **Version Control:** Git & GitHub
- **Environment:** Linux (Kali), Virtualenv

---

## Installation & Setup

```bash
# Clone repository
git clone https://github.com/eKidenge/KACAF.git
cd KACAF

# Create virtual environment
python3 -m venv django_env
source django_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```


## Security & Best Practices

* Environment variables for sensitive data
* Role-based authorization
* Modular Django apps
* Clean separation of concerns

---

## Development Status

* Core template architecture implemented
* Dashboard structure completed
* Modules structured and ready for backend integration

---

## Contribution

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Submit a pull request

---

## License

This project is licensed under the  **MIT License** .

---

## Author

**Elisha Kidenge**

BSc Physics | MSc Computer Science

GitHub: [https://github.com/eKidenge](https://github.com/eKidenge)

---

## Organization

**Kenya Association of Community Action Facilitators (KACAF)**

Empowering communities through action, governance, and technology.
