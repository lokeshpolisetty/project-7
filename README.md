# SmartTutor - AI-Powered Online Tutoring Platform

A comprehensive online tutoring platform built with HTML, CSS, Bootstrap, Python (Flask), PostgreSQL, and Google Gemini AI integration.

## Features

### Core Features
- **User Authentication**: Secure login and registration for students and tutors
- **Role-based Dashboards**: Separate interfaces for students and tutors
- **Tutor Discovery**: Search and filter tutors by subject, rating, and price
- **Session Booking**: Easy scheduling system with calendar integration
- **Profile Management**: Comprehensive user profiles with stats and settings
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5

### AI-Powered Features
- **AI Tutor Assistant**: Powered by Google Gemini AI
- **Step-by-Step Explanations**: Get detailed explanations for complex topics
- **Practice Problem Generation**: Create unlimited practice problems with solutions
- **Interactive Quizzes**: Generate custom quizzes to test knowledge
- **Study Notes Creation**: Comprehensive study notes with key concepts
- **Conversation History**: Save and review past AI interactions

## Technology Stack

- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Backend**: Python Flask
- **Database**: PostgreSQL
- **AI Integration**: Google Gemini AI
- **Icons**: Font Awesome 6
- **Images**: Pexels stock photos

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smarttutor
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   - Install PostgreSQL
   - Create a database named `smarttutor`
   - Run the SQL script in `supabase/migrations/20250706094251_cool_sun.sql`

4. **Configure environment variables**
   - Copy `.env` file and update:
     - Database connection string
     - Secret key
     - **Gemini API key** (get from Google AI Studio)

5. **Get Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file as `GEMINI_API_KEY`

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open your browser and go to `http://localhost:5000`

## Demo Accounts

- **Student**: email: `student@demo.com`, password: `demo123`
- **Tutor**: email: `tutor@demo.com`, password: `demo123`

## AI Tutor Features

### Question Types Supported
- **General Questions**: Ask anything about academic topics
- **Step-by-Step Explanations**: Get detailed breakdowns of complex concepts
- **Practice Problems**: Generate problems with solutions for any subject
- **Quiz Creation**: Create custom quizzes with multiple choice questions
- **Study Notes**: Generate comprehensive study materials

### Supported Subjects
- Mathematics
- Physics
- Chemistry
- Biology
- English
- History
- Programming
- Science (General)

### AI Conversation Types
1. **General**: Basic Q&A format
2. **Explanation**: Detailed step-by-step explanations
3. **Practice**: Generate practice problems with solutions
4. **Quiz**: Create multiple-choice quizzes
5. **Study Notes**: Comprehensive study materials

## Project Structure

```
smarttutor/
├── app.py                          # Main Flask application with AI integration
├── requirements.txt                # Python dependencies including Gemini AI
├── .env                           # Environment variables (includes GEMINI_API_KEY)
├── supabase/migrations/           # Database schema
├── templates/                     # HTML templates
│   ├── base.html                 # Updated with AI Tutor navigation
│   ├── index.html                # Updated with AI features showcase
│   ├── ai_tutor.html             # New AI chat interface
│   ├── student_dashboard.html    # Updated with AI quick access
│   └── ...                       # Other existing templates
└── static/                       # Static assets
    ├── css/style.css
    └── js/main.js
```

## Key Features

### For Students
- Browse and search tutors
- Book tutoring sessions
- **Chat with AI tutor for instant help**
- **Generate practice problems and quizzes**
- **Get step-by-step explanations**
- View upcoming and past sessions
- Rate and review tutors
- Track learning progress

### For Tutors
- Manage teaching schedule
- View student sessions
- Track earnings and ratings
- Update profile and subjects
- **Access AI tools to help students**

### AI Tutor Capabilities
- **Natural Language Processing**: Understands questions in plain English
- **Subject-Aware Responses**: Tailored answers based on selected subject
- **Multiple Response Types**: Explanations, problems, quizzes, notes
- **Conversation Memory**: Saves chat history for review
- **Real-time Responses**: Instant AI-generated answers

## Database Schema

### Users Table
- User authentication and profile information
- Role-based access (student/tutor)
- Tutor-specific fields (hourly rate, subjects, rating)

### Tutoring Sessions Table
- Session scheduling and management
- Status tracking (scheduled, completed, cancelled)
- Rating and review system

### AI Conversations Table (New)
- Stores AI chat history
- Conversation types and subjects
- User-specific conversation tracking

## API Integration

### Google Gemini AI
- **Model**: gemini-pro
- **Features**: Text generation, conversation, explanations
- **Rate Limits**: Managed through Google AI Studio
- **Error Handling**: Graceful fallbacks for API issues

## Security Features

- Password hashing using Werkzeug
- Session management
- SQL injection prevention
- API key protection
- Input sanitization for AI queries

## Future Enhancements

- Real-time video chat integration
- Payment processing
- Advanced AI features (image recognition, voice chat)
- Mobile app
- Email notifications
- Calendar synchronization
- AI-powered tutor matching
- Personalized learning paths

## AI Usage Guidelines

### Best Practices
- Ask specific questions for better responses
- Include subject context when possible
- Use conversation types for targeted help
- Review generated content for accuracy

### Limitations
- AI responses should be verified for complex topics
- Not a replacement for human tutors
- May have knowledge cutoff limitations
- Requires internet connection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (including AI features)
5. Submit a pull request

## Environment Variables

```env
DATABASE_URL=postgresql://username:password@localhost:5432/smarttutor
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
GEMINI_API_KEY=your-gemini-api-key-here
```

## License

This project is licensed under the MIT License.

## Support

For issues related to:
- **Platform functionality**: Create an issue in the repository
- **AI features**: Check Google AI Studio documentation
- **Database**: Refer to PostgreSQL documentation

---

**Powered by Google Gemini AI** - Experience the future of personalized learning!