# AWS CLF-C02 Quiz Trainer

A Flask-based web application for practicing AWS Certified Cloud Practitioner (CLF-C02) exam questions with progress tracking and mastery system.

## Features

- **Interactive Quiz Interface**: Clean, responsive web interface
- **Progress Tracking**: Track correct/incorrect answers per question
- **Mastery System**: Questions require 4 correct answers to be marked as mastered
- **Domain Filtering**: Practice questions by specific AWS domains
- **Missed Questions Review**: Focus on questions you've previously answered incorrectly
- **Detailed Explanations**: Each question includes explanation for the correct answer

## Technologies

- **Backend**: Python, Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mrezakhani/
   cd aws-certification-trainer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python web_app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
├── web_app.py          # Flask web application
├── aws_quiz.db         # SQLite database with quiz questions
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── index.html
│   ├── quiz.html
│   ├── results.html
│   └── review.html
└── static/
    └── style.css
```

## Usage

1. Select a domain or practice all questions
2. Choose number of questions for your quiz session
3. Answer questions and receive immediate feedback
4. Review your results and track mastery progress
5. Use "Missed Questions" to practice questions you got wrong

## Database

The application includes 30 sample questions covering all four AWS CLF-C02 exam domains:
- Cloud Concepts
- Security and Compliance
- Technology and Services
- Billing and Pricing

## License

This project is for educational purposes. But I can write any project you need for you at a fair price. Please contact me under this E-Mail: rezakhani.mojgan@gmail.com