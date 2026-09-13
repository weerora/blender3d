export const objects = [
  { id: 'chair', icon: 'chair', title: 'เก้าอี้ทำงาน', en: 'The everyday chair', tag: '01 / FURNITURE', description: 'เก้าอี้ตาข่ายที่ออกแบบให้เป็นมุมทำงานสบาย ๆ ลองหมุนเพื่อดูโครงและพนักพิงรอบตัว', action: 'หมุนเก้าอี้ 90°', type: 'หมุนได้', focus: [0.05, 0.75, -0.32] },
  { id: 'monitors', icon: 'monitor', title: 'หน้าจอคู่', en: 'Room for ideas', tag: '02 / WORKSPACE', description: 'สลับจากงานออกแบบสถาปัตยกรรมเป็นหน้าจอโหมดโฟกัส หรือปิดจอเมื่อถึงเวลาพัก', action: 'เปลี่ยนหน้าจอ', type: '3 โหมด', focus: [0.05, 1.2, -1.2] },
  { id: 'lamp', icon: 'lamp', title: 'โคมไฟโต๊ะ', en: 'A little warm light', tag: '03 / LIGHTING', description: 'เติมแสงอุ่นให้โต๊ะทำงาน เปิด–ปิดโคมไฟและลองใช้ร่วมกับบรรยากาศช่วงกลางคืน', action: 'ปิดโคมไฟ', type: 'เปิด–ปิด', focus: [-0.8, 1.06, -1.15] },
  { id: 'door', icon: 'door', title: 'ประตูห้อง', en: 'Come on in', tag: '04 / ARCHITECTURE', description: 'เปิดประตูเข้ามาสำรวจห้องขนาด 3.5 × 3.5 เมตร บานประตูหมุนรอบบานพับจริงในโมเดล', action: 'เปิดประตู', type: 'เปิด–ปิด', focus: [-1.65, 1.05, 1.23] },
  { id: 'drawers', icon: 'drawer', title: 'ลิ้นชัก', en: 'Everything in its place', tag: '05 / STORAGE', description: 'เลือกเปิดลิ้นชักแต่ละชั้นเพื่อสำรวจตู้เก็บของใต้โต๊ะ แล้วปิดกลับเมื่อจัดโต๊ะเสร็จ', action: 'เปิดลิ้นชัก', type: '4 ชั้น', focus: [0.96, 0.4, -0.8] },
  { id: 'blinds', icon: 'blinds', title: 'มู่ลี่หน้าต่าง', en: 'Let the day in', tag: '06 / DAYLIGHT', description: 'ยกมู่ลี่ขึ้นเพื่อเปิดรับแสงและวิวสีเขียว หรือปรับกลับเพื่อสร้างมุมทำงานที่เป็นส่วนตัว', action: 'ยกมู่ลี่', type: 'ปรับระดับ', focus: [-1.7, 1.7, -0.8] },
  { id: 'logo', icon: 'sparkle', title: 'ไฟโลโก้', en: 'Make it your studio', tag: '07 / LIGHTING', description: 'แสงอุ่นหลังตัวอักษร WEER ช่วยขับพื้นผิวไม้ไผ่และสร้างเอกลักษณ์ให้ผนังห้อง', action: 'ปิดไฟโลโก้', type: 'เปิด–ปิด', focus: [-0.15, 1.95, -1.62] },
  { id: 'ac', icon: 'ac', title: 'เครื่องปรับอากาศ', en: 'Find your comfort', tag: '08 / ATMOSPHERE', description: 'ทดลองเปิดระบบทำความเย็นและปรับอุณหภูมิจำลอง พร้อมเส้นลมที่แสดงสถานะบนตัวเครื่อง', action: 'เปิดเครื่องปรับอากาศ', type: 'จำลอง', focus: [1.52, 2.4, -1.5] },
  { id: 'radio', icon: 'radio', title: 'เสียงบรรยากาศ', en: 'Settle into your rhythm', tag: '09 / SOUND', description: 'เปิดเสียง ambient เบา ๆ จากลำโพงบนโต๊ะ เสียงสังเคราะห์ทำงานในเบราว์เซอร์และปรับระดับได้', action: 'เปิดเสียงบรรยากาศ', type: 'เล่นเสียง', focus: [1.05, 0.94, -1.2] },
] as const;
export type ObjectId = typeof objects[number]['id'];
export type Mode = 'day' | 'night';
export type View = 'overview' | 'desk' | 'lounge';
