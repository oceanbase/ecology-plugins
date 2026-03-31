import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

// GET - list reviews for course
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const reviews = await query(
      'SELECT `id`, `course_id`, `student_name`, `rating`, `comment`, `created_at` FROM `reviews` WHERE `course_id` = ? ORDER BY `created_at` DESC',
      [params.id]
    );

    return NextResponse.json({ success: true, data: reviews });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

// POST - add review
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const { student_name, rating, comment } = body;

    if (!student_name || !rating) {
      return NextResponse.json(
        { success: false, error: 'Student name and rating are required' },
        { status: 400 }
      );
    }

    if (rating < 1 || rating > 5) {
      return NextResponse.json(
        { success: false, error: 'Rating must be between 1 and 5' },
        { status: 400 }
      );
    }

    const result = await query(
      'INSERT INTO `reviews` (`course_id`, `student_name`, `rating`, `comment`) VALUES (?, ?, ?, ?)',
      [params.id, student_name, rating, comment || null]
    );

    const insertResult = result as any;
    return NextResponse.json({
      success: true,
      data: {
        id: insertResult.insertId,
        course_id: parseInt(params.id),
        student_name,
        rating,
        comment,
      },
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

