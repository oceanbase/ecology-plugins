'use client';

import { useState, useEffect } from 'react';

interface Course {
  id: number;
  code: string;
  name: string;
  description?: string;
  instructor: string;
  department: string;
  credits: number;
  capacity: number;
  enrolled: number;
  semester: string;
}

interface Review {
  id: number;
  course_id: number;
  student_name: string;
  rating: number;
  comment?: string;
  created_at: string;
}

export default function Home() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    instructor: '',
    department: '',
    credits: 3,
    capacity: 30,
    semester: 'Fall 2024',
  });

  const [reviewForm, setReviewForm] = useState({
    student_name: '',
    rating: 0,
    comment: '',
  });

  const [capacityForm, setCapacityForm] = useState({ capacity: 30 });

  const fetchCourses = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (departmentFilter) params.append('department', departmentFilter);
      if (semesterFilter) params.append('semester', semesterFilter);
      
      const response = await fetch(`/api/courses?${params.toString()}`);
      const result = await response.json();

      if (result.success) {
        setCourses(result.data);
      } else {
        setError(result.error || 'Failed to fetch courses');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch courses');
    } finally {
      setLoading(false);
    }
  };

  const fetchCourseDetails = async (courseId: number) => {
    try {
      const response = await fetch(`/api/courses/${courseId}`);
      const result = await response.json();

      if (result.success) {
        setSelectedCourse(result.data);
        fetchReviews(courseId);
        setShowModal(true);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch course details');
    }
  };

  const fetchReviews = async (courseId: number) => {
    try {
      const response = await fetch(`/api/courses/${courseId}/reviews`);
      const result = await response.json();

      if (result.success) {
        setReviews(result.data);
      }
    } catch (err: any) {
      console.error('Failed to fetch reviews:', err);
    }
  };

  const createCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        setSuccess('Course created successfully!');
        setFormData({
          code: '',
          name: '',
          description: '',
          instructor: '',
          department: '',
          credits: 3,
          capacity: 30,
          semester: 'Fall 2024',
        });
        setShowCreateModal(false);
        fetchCourses();
      } else {
        setError(result.error || 'Failed to create course');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create course');
    }
  };

  const updateCapacity = async (courseId: number) => {
    try {
      setError(null);
      setSuccess(null);

      const response = await fetch(`/api/courses/${courseId}/capacity`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(capacityForm),
      });

      const result = await response.json();

      if (result.success) {
        setSuccess('Course capacity updated successfully!');
        if (selectedCourse) {
          setSelectedCourse({ ...selectedCourse, capacity: capacityForm.capacity });
        }
        fetchCourses();
      } else {
        setError(result.error || 'Failed to update capacity');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update capacity');
    }
  };

  const addReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourse || reviewForm.rating === 0) {
      setError('Please provide a rating');
      return;
    }

    try {
      setError(null);
      setSuccess(null);

      const response = await fetch(`/api/courses/${selectedCourse.id}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewForm),
      });

      const result = await response.json();

      if (result.success) {
        setSuccess('Review added successfully!');
        setReviewForm({ student_name: '', rating: 0, comment: '' });
        setShowReviewForm(false);
        fetchReviews(selectedCourse.id);
      } else {
        setError(result.error || 'Failed to add review');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to add review');
    }
  };

  const deleteReview = async (reviewId: number) => {
    if (!confirm('Are you sure you want to delete this review?')) return;

    try {
      setError(null);
      setSuccess(null);

      const response = await fetch(`/api/reviews/${reviewId}`, {
        method: 'DELETE',
      });

      const result = await response.json();

      if (result.success) {
        setSuccess('Review deleted successfully!');
        if (selectedCourse) {
          fetchReviews(selectedCourse.id);
        }
      } else {
        setError(result.error || 'Failed to delete review');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete review');
    }
  };

  const deleteCourse = async (courseId: number) => {
    if (!confirm('Are you sure you want to delete this course? This will also delete all reviews.')) return;

    try {
      setError(null);
      setSuccess(null);

      const response = await fetch(`/api/courses/${courseId}`, {
        method: 'DELETE',
      });

      const result = await response.json();

      if (result.success) {
        setSuccess('Course deleted successfully!');
        setShowModal(false);
        setSelectedCourse(null);
        fetchCourses();
      } else {
        setError(result.error || 'Failed to delete course');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete course');
    }
  };

  const departments = Array.from(new Set(courses.map(c => c.department)));

  useEffect(() => {
    fetchCourses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departmentFilter, semesterFilter]);

  return (
    <div className="container">
      <div className="header">
        <h1>🎓 UniSelect Course</h1>
        <p>
          University course selection admin · Manage courses, view details, add/delete reviews, edit capacity ·
          Powered by OceanBase Cloud, Next.js &amp; Vercel
        </p>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <div className="table-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>Courses</h2>
          <button
            className="button"
            onClick={() => setShowCreateModal(true)}
          >
            ➕ New course
          </button>
        </div>
        <div className="filters">
          <div className="filter-group">
            <label htmlFor="department-filter">Department</label>
            <select
              id="department-filter"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
            >
              <option value="">All departments</option>
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label htmlFor="semester-filter">Semester</label>
            <select
              id="semester-filter"
              value={semesterFilter}
              onChange={(e) => setSemesterFilter(e.target.value)}
            >
              <option value="">All semesters</option>
              <option value="Fall 2024">Fall 2024</option>
              <option value="Spring 2024">Spring 2024</option>
              <option value="Summer 2024">Summer 2024</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : courses.length === 0 ? (
          <div className="empty">No courses yet</div>
        ) : (
          <div className="course-grid">
            {courses.map((course) => (
              <div key={course.id} className="course-card" onClick={() => fetchCourseDetails(course.id)}>
                <div className="course-header">
                  <span className="course-code">{course.code}</span>
                </div>
                <div className="course-name">{course.name}</div>
                <div className="course-info">👨‍🏫 {course.instructor}</div>
                <div className="course-info">🏛️ {course.department}</div>
                <div className="course-info">📚 {course.credits} credits | 📅 {course.semester}</div>
                <div className="course-meta">
                  <div className="capacity-info">
                    Enrolled: <strong>{course.enrolled}</strong> / <strong>{course.capacity}</strong>
                  </div>
                  <div style={{ 
                    color: course.enrolled >= course.capacity ? '#dc3545' : '#28a745',
                    fontSize: '0.85rem',
                    fontWeight: 600
                  }}>
                    {course.enrolled >= course.capacity ? 'Full' : 'Open'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showModal && selectedCourse && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedCourse.name}</h2>
              <button className="close-button" onClick={() => setShowModal(false)}>×</button>
            </div>

            <div>
              <div style={{ marginBottom: '1rem' }}>
                <strong>Code:</strong> {selectedCourse.code}
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <strong>Instructor:</strong> {selectedCourse.instructor}
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <strong>Department:</strong> {selectedCourse.department}
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <strong>Credits:</strong> {selectedCourse.credits} | <strong>Semester:</strong> {selectedCourse.semester}
              </div>
              {selectedCourse.description && (
                <div style={{ marginBottom: '1rem', color: '#666', lineHeight: '1.6' }}>
                  <strong>Description:</strong><br />
                  {selectedCourse.description}
                </div>
              )}

              <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#f8f9fa', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div>
                    <strong>Capacity:</strong> {selectedCourse.enrolled} / {selectedCourse.capacity} enrolled
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input
                      type="number"
                      value={capacityForm.capacity}
                      onChange={(e) => setCapacityForm({ capacity: parseInt(e.target.value) || 30 })}
                      min="1"
                      style={{ width: '80px', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                    <button
                      className="button button-small"
                      onClick={() => updateCapacity(selectedCourse.id)}
                    >
                      Update capacity
                    </button>
                  </div>
                </div>
              </div>

              <div className="reviews-section">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3>Reviews ({reviews.length})</h3>
                  <button
                    className="button button-small"
                    onClick={() => setShowReviewForm(!showReviewForm)}
                  >
                    {showReviewForm ? 'Cancel' : 'Add review'}
                  </button>
                </div>

                {showReviewForm && (
                  <form onSubmit={addReview} style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '6px', marginBottom: '1rem' }}>
                    <div className="form-group">
                      <label>Student name *</label>
                      <input
                        type="text"
                        value={reviewForm.student_name}
                        onChange={(e) => setReviewForm({ ...reviewForm, student_name: e.target.value })}
                        required
                        placeholder="Your name"
                      />
                    </div>
                    <div className="form-group">
                      <label>Rating *</label>
                      <div className="rating-input">
                        <div className="rating-stars">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <span
                              key={star}
                              className={`star ${reviewForm.rating >= star ? 'active' : ''}`}
                              onClick={() => setReviewForm({ ...reviewForm, rating: star })}
                            >
                              ★
                            </span>
                          ))}
                        </div>
                        <span style={{ marginLeft: '0.5rem', color: '#666' }}>
                          {reviewForm.rating > 0 ? `${reviewForm.rating} / 5` : 'Select a rating'}
                        </span>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Comment</label>
                      <textarea
                        value={reviewForm.comment}
                        onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                        placeholder="Write your review..."
                      />
                    </div>
                    <button type="submit" className="button">Submit review</button>
                  </form>
                )}

                {reviews.length === 0 ? (
                  <div className="empty">No reviews yet</div>
                ) : (
                  reviews.map((review) => (
                    <div key={review.id} className="review-item">
                      <div className="review-header">
                        <span className="review-author">{review.student_name}</span>
                        <div>
                          <span className="review-rating">
                            {'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}
                          </span>
                          <button
                            className="button button-danger button-small"
                            style={{ marginLeft: '1rem' }}
                            onClick={() => deleteReview(review.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                      {review.comment && (
                        <div className="review-comment">{review.comment}</div>
                      )}
                      <div className="review-date">
                        {new Date(review.created_at).toLocaleString('en-US')}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button
                  className="button button-danger"
                  onClick={() => deleteCourse(selectedCourse.id)}
                >
                  Delete course
                </button>
                <button
                  className="button button-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create course</h2>
              <button className="close-button" onClick={() => setShowCreateModal(false)}>×</button>
            </div>

            <form onSubmit={createCourse}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                <div className="form-group">
                  <label htmlFor="code">Course code *</label>
                  <input
                    type="text"
                    id="code"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    required
                    placeholder="e.g. CS101"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="name">Course name *</label>
                  <input
                    type="text"
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    placeholder="e.g. Introduction to Computer Science"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="instructor">Instructor *</label>
                  <input
                    type="text"
                    id="instructor"
                    value={formData.instructor}
                    onChange={(e) => setFormData({ ...formData, instructor: e.target.value })}
                    required
                    placeholder="e.g. Dr. Sarah Johnson"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="department">Department *</label>
                  <input
                    type="text"
                    id="department"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    required
                    placeholder="e.g. Computer Science"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="credits">Credits</label>
                  <input
                    type="number"
                    id="credits"
                    value={formData.credits}
                    onChange={(e) => setFormData({ ...formData, credits: parseInt(e.target.value) || 3 })}
                    min="1"
                    max="6"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="capacity">Capacity</label>
                  <input
                    type="number"
                    id="capacity"
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) || 30 })}
                    min="1"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="semester">Semester</label>
                  <select
                    id="semester"
                    value={formData.semester}
                    onChange={(e) => setFormData({ ...formData, semester: e.target.value })}
                  >
                    <option value="Fall 2024">Fall 2024</option>
                    <option value="Spring 2024">Spring 2024</option>
                    <option value="Summer 2024">Summer 2024</option>
                  </select>
                </div>
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Course description..."
                    style={{ minHeight: '100px' }}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => {
                    setShowCreateModal(false);
                    setFormData({
                      code: '',
                      name: '',
                      description: '',
                      instructor: '',
                      department: '',
                      credits: 3,
                      capacity: 30,
                      semester: 'Fall 2024',
                    });
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="button">Create course</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
