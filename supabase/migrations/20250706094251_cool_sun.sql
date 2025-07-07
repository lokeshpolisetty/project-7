-- SmartTutor Database Setup
-- Run this script to set up the PostgreSQL database

-- Create database (run this as postgres user)
-- CREATE DATABASE smarttutor;

-- Connect to the smarttutor database and run the following:

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'tutor')),
    avatar VARCHAR(255),
    bio TEXT,
    hourly_rate DECIMAL(10,2),
    subjects TEXT[],
    rating DECIMAL(3,2) DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tutoring sessions table
CREATE TABLE IF NOT EXISTS tutoring_sessions (
    id SERIAL PRIMARY KEY,
    tutor_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    duration INTEGER NOT NULL, -- in minutes
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_tutor ON tutoring_sessions(tutor_id);
CREATE INDEX IF NOT EXISTS idx_sessions_student ON tutoring_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_scheduled ON tutoring_sessions(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON tutoring_sessions(status);

-- Insert sample data
INSERT INTO users (email, password_hash, name, role, bio, hourly_rate, subjects, rating, total_sessions) VALUES
('tutor@demo.com', 'pbkdf2:sha256:260000$salt$hash', 'Dr. Sarah Johnson', 'tutor', 'PhD in Mathematics with 8 years of teaching experience. Specializes in calculus and algebra.', 45.00, ARRAY['Mathematics', 'Physics'], 4.9, 245),
('student@demo.com', 'pbkdf2:sha256:260000$salt$hash', 'Alex Smith', 'student', 'High school student passionate about learning.', NULL, NULL, 0, 24),
('tutor2@demo.com', 'pbkdf2:sha256:260000$salt$hash', 'Prof. Mike Chen', 'tutor', 'Senior Software Engineer turned educator. Expert in Python, JavaScript, and web development.', 55.00, ARRAY['Programming', 'Computer Science'], 4.8, 189),
('tutor3@demo.com', 'pbkdf2:sha256:260000$salt$hash', 'Dr. Emily Rodriguez', 'tutor', 'Medical doctor with extensive knowledge in biochemistry and molecular biology.', 42.00, ARRAY['Chemistry', 'Biology'], 4.9, 198)
ON CONFLICT (email) DO NOTHING;

-- Note: In a real application, you would use proper password hashing
-- For demo purposes, the password for all accounts is 'demo123'
-- You'll need to generate proper hashes using Werkzeug's generate_password_hash function