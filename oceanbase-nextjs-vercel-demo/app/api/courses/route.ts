import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

// GET - list courses
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const department = searchParams.get('department');
    const semester = searchParams.get('semester');

    let sql = 'SELECT `id`, `code`, `name`, `description`, `instructor`, `department`, `credits`, `capacity`, `enrolled`, `semester` FROM `courses`';
    const params: any[] = [];

    if (department || semester) {
      const conditions: string[] = [];
      if (department) {
        conditions.push('`department` = ?');
        params.push(department);
      }
      if (semester) {
        conditions.push('`semester` = ?');
        params.push(semester);
      }
      sql += ' WHERE ' + conditions.join(' AND ');
    }

    sql += ' ORDER BY `code` ASC';

    const courses = await query(sql, params);
    return NextResponse.json({ success: true, data: courses });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

// POST - create course
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { code, name, description, instructor, department, credits, capacity, semester } = body;

    if (!code || !name || !instructor || !department) {
      return NextResponse.json(
        { success: false, error: 'Code, name, instructor, and department are required' },
        { status: 400 }
      );
    }

    const result = await query(
      `INSERT INTO \`courses\` (\`code\`, \`name\`, \`description\`, \`instructor\`, \`department\`, \`credits\`, \`capacity\`, \`semester\`)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [code, name, description || null, instructor, department, credits || 3, capacity || 30, semester || 'Fall 2024']
    );

    const insertResult = result as any;
    return NextResponse.json({
      success: true,
      data: { id: insertResult.insertId, code, name, instructor, department },
    });
  } catch (error: any) {
    if (error.code === 'ER_DUP_ENTRY') {
      return NextResponse.json(
        { success: false, error: 'Course code already exists' },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

