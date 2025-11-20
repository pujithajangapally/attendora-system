INSERT INTO students (
    id,
    name,
    roll_no,
    class_name,
    phone_number,
    encoding
  )
VALUES (
    id:intINSERT INTO students (
        id,
        name,
        roll_no,
        class_name,
        phone_number,
        encoding
      )
    VALUES (
        id:int,
        'name:varchar',
        'roll_no:varchar',
        'class_name:varchar',
        'phone_number:varchar',
        'encoding:blob'
      );,
    'name:varchar',
    'roll_no:varchar',
    'class_name:varchar',
    'phone_number:varchar',
    'encoding:blob'
  );INSERT INTO students_attendora (
    student_id,
    roll_no,
    name,
    face_encoding,
    phone_number
  )
VALUES (
    student_id:intINSERT INTO attendance_attendora (
        id,
        roll_no,
        date,
        period1,
        period2,
        period3,
        period4,
        period5,
        period6,
        period7,
        period8
      )
    VALUES (
        id:intINSERT INTO students (
            id,
            name,
            roll_no,
            class_name,
            phone_number,
            encoding
          )
        VALUES (
            id:int,
            'name:varchar',
            'roll_no:varchar',
            'class_name:varchar',
            'phone_number:varchar',
            'encoding:blob'
          );,
        'roll_no:varchar',
        'date:date',
        'period1:varchar',
        'period2:varchar',
        'period3:varchar',
        'period4:varchar',
        'period5:varchar',
        'period6:varchar',
        'period7:varchar',
        'period8:varchar'
      );,
    'roll_no:varchar',
    'name:varchar',
    'face_encoding:json',
    'phone_number:varchar'
  );