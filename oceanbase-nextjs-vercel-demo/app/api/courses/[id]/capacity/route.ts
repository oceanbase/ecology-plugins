import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

// PUT - update course capacity
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const { capacity } = body;

    if (!capacity || capacity < 0) {
      return NextResponse.json(
        { success: false, error: 'Valid capacity is required' },
        { status: 400 }
      );
    }

    await query(
      'UPDATE `courses` SET `capacity` = ? WHERE `id` = ?',
      [capacity, params.id]
    );

    const courses = await query(
      'SELECT `id`, `code`, `name`, `capacity`, `enrolled` FROM `courses` WHERE `id` = ?',
      [params.id]
    );

    const courseArray = courses as any[];
    return NextResponse.json({
      success: true,
      data: courseArray[0],
      message: 'Course capacity updated successfully',
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

