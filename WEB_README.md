# WEER Studio — interactive room

เว็บห้องทำงานจาก `Office_Studio_v02.blend` ใช้ Vite + Three.js + TypeScript และโมเดล GLB จริงจาก Blender

## เริ่มใช้งาน

```sh
npm ci
npm run dev
```

เปิด URL ที่ Vite แสดง เช่น `http://127.0.0.1:5173/`

```sh
npm run build
npm run preview
```

นำโฟลเดอร์ `dist/` ไปให้บริการด้วย static hosting ได้ ไม่ต้องมี backend เปิด `index.html` ผ่าน `file://` โดยตรงไม่ได้

ใช้ Node 24 บนเครื่องนี้ โดย lockfile บันทึกแพ็กเกจที่ตรวจสอบแล้ว: Vite 8.3.0, Three.js 0.186.0, TypeScript 7.0.2

## การโต้ตอบ

| วัตถุ | การทำงาน |
| --- | --- |
| เก้าอี้ | หมุนครั้งละ 90 องศา |
| จอคู่ | สลับภาพงานออกแบบ / Focus / ปิดจอ |
| โคมไฟ | เปิด–ปิดวัสดุเรืองแสงและแสงบนโต๊ะ |
| ประตู | เปิด–ปิดรอบจุดบานพับ พร้อมช่องประตูจริง |
| ลิ้นชัก | เลือกและเปิด–ปิดแต่ละชั้น มีถาดและผนังด้านใน |
| มู่ลี่ | ยกขึ้นและลดลง |
| โลโก้ | เปิด–ปิดไฟอุ่นหลังตัวอักษร |
| แอร์ | เปิด–ปิดเส้นลมและปรับอุณหภูมิจำลอง |
| ลำโพง | เล่นเสียง ambient ที่สังเคราะห์ใน Web Audio และปรับระดับเสียง |

ลากเพื่อหมุนห้อง คลิกขวาลากเพื่อเลื่อน ใช้ล้อเมาส์ซูม มือถือใช้หนึ่งนิ้วหมุนและสองนิ้วเลื่อน/ซูม เลือกวัตถุจากโมเดล จุดเลือก หรือปุ่มในแผงควบคุม

มีมุมกล้องภาพรวม/โต๊ะ/มุมพักผ่อน โหมดกลางวัน/กลางคืน การชมรอบห้อง ปุ่มซ่อนจุดเลือก การตั้งค่าความละเอียด/เงา/ความสว่าง และปุ่มเต็มหน้าจอ ใช้ Tab/Enter กับปุ่ม, R กลับมุมเริ่มต้น, Esc ยกเลิกการเลือก

## โครงสร้าง

- `src/room.ts`: renderer, GLB loading, picking, lights, cameras, animation และส่วนภายในประตู/ลิ้นชัก
- `src/main.ts`: หน้าตาเว็บ แผงควบคุม dialog และการเชื่อมต่อ state
- `src/catalog.ts`: รายชื่อวัตถุ คำอธิบายและตำแหน่งจุดเลือก
- `src/audio.ts`: ambient audio แบบ local ไม่มี autoplay
- `public/models/office-studio.glb`: โมเดลบีบอัดพร้อมใช้งาน
- `scripts/export_web_asset.py`: ประเมิน geometry จากสำเนาฉาก Blender แล้วรวมเป็นกลุ่มสำหรับเว็บ โดยไม่บันทึกทับ `.blend`
- `scripts/optimize-asset.mjs`: deduplicate, weld, prune, Meshopt compression และตรวจชื่อกลุ่ม

## โมเดลและประสิทธิภาพ

โมเดล GLB ลดจากประมาณ 30.7 MB เหลือ 7.54 MB คงไว้ 21 กลุ่ม ชิ้นส่วนต้นฉบับมากกว่า 2,000 ชิ้นรวมตามการโต้ตอบและวัสดุเพื่อลด draw calls ใช้ Meshopt decoder ที่รวมมากับแอป ไม่มีการเรียก CDN เพื่อโหลดโมเดลหรือ decoder และฟอนต์เก็บในโปรเจกต์

ใช้ dynamic lighting หนึ่งแสงหลักที่สร้างเงาและไฟตกแต่งที่ไม่สร้าง shadow maps เพิ่ม สำหรับมือถือหรือ GPU ช้า ให้ปิดความละเอียดสูงหรือเงาใน Settings การรองรับ responsive UI ไม่ได้หมายความว่าได้ benchmark บนฮาร์ดแวร์มือถือทุกรุ่น

วัสดุ procedural ของ Blender ถูกแปลงเป็น PBR สีพื้นและค่าความหยาบสำหรับ GLB ยังไม่ได้ bake ทุกพื้นผิวและแสงแบบ Cycles จึงคง geometry ของห้องไว้ แต่ภาพในเว็บไม่เหมือนภาพเรนเดอร์ Blender ทุกพิกเซล ไม่ใช้ภาพเรนเดอร์แบนแทนโมเดล

## การอัปเดตโมเดล

1. เปิด `Office_Studio_v02.blend` ใน Blender
2. รัน `scripts/export_web_asset.py` ผ่าน Blender MCP หรือ Scripting workspace
3. รัน `npm run asset:optimize`
4. รัน `npm run build` และตรวจเว็บอีกครั้ง

ไฟล์ intermediate และรายงาน export/optimization อยู่ใน `assets-source/` ซึ่งไม่ใช่ไฟล์ที่ส่งขึ้นเว็บ

glTF Validator ไม่พบ errors หรือ warnings ในโครงสร้างมาตรฐาน มี informational notice ว่า validator ไม่ตรวจข้อมูลภายในส่วนขยาย Meshopt จึงต้องตรวจการ decode ด้วย GLTFLoader ในเบราว์เซอร์ด้วย

## แหล่งอ้างอิงทางเทคนิค

- [Vite guide](https://vite.dev/guide/)
- [Three.js GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html)
- [Three.js OrbitControls](https://threejs.org/docs/pages/OrbitControls.html)
- [Three.js Raycaster](https://threejs.org/docs/pages/Raycaster.html)
- [glTF Transform](https://gltf-transform.dev/)
