import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

// GET - course by id
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const courses = await query(
      'SELECT `id`, `code`, `name`, `description`, `instructor`, `department`, `credits`, `capacity`, `enrolled`, `semester` FROM `courses` WHERE `id` = ?',
      [params.id]
    );

    const courseArray = courses as any[];
    if (courseArray.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Course not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true, data: courseArray[0] });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

// DELETE - remove course
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    await query('DELETE FROM `courses` WHERE `id` = ?', [params.id]);
    return NextResponse.json({ success: true, message: 'Course deleted successfully' });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

