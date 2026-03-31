import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

// DELETE - remove a review
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    await query('DELETE FROM `reviews` WHERE `id` = ?', [params.id]);
    return NextResponse.json({ success: true, message: 'Review deleted successfully' });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

