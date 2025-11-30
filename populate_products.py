#!/usr/bin/env python3
"""
Populate the database with products matching the brand folders
"""
import os
import sys

sys.path.append(".")

from app.main import Base, Product, SessionLocal, engine


def populate_products():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Clear existing products
        db.query(Product).delete()

        # Products based on the brand folders and descriptions
        products_data = [
            # Esko Switch products
            {
                "name": "Esko Switch Starter Kit",
                "description": "Starter Kit และ Cartridge หลากหลายรสชาติ - ชุดเริ่มต้นสูบไอพร้อม cartridge แทนที่ได้",
                "price": 79.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/esko-switch-starter-kit.jpg",
            },
            {
                "name": "Esko Switch Apple Aloe",
                "description": "Cartridge รสแอปเปิ้ลอะลัว สดชื่นจากธรรมชาติ",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Apple Aloe_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Blueberry",
                "description": "Cartridge รสบลูเบอร์รี่ หอมหวานสดชื่น",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Blueberry_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Cola",
                "description": "Cartridge รสโคล่า หอมเปรี้ยวสดชื่น",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Cola_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Cool Mint",
                "description": "Cartridge รสเย็นมิ้นต์ หอมสดชื่น",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Cool Mint_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Grape",
                "description": "Cartridge รองุ่น หอมหวานจากธรรมชาติ",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Grape_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Honeydew",
                "description": "Cartridge รสเมล่อน หอมหวานอร่อย",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Honeydew_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Lychee",
                "description": "Cartridge รสลิ้นจี่ หอมหวานพิเศษ",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Lychee_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Mix Berry",
                "description": "Cartridge รสเบอร์รี่รวม หอมหวานหลากสีสัน",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Mix Berry_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Pineapple",
                "description": "Cartridge รสสับปะรด หอมหวานฉ่ำ",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Pineapple_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Pink Guava",
                "description": "Cartridge รสฝรั่งชมพู่ หอมหวานอร่อย",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Pink Guava_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Strawberry",
                "description": "Cartridge รสสตรอเบอร์รี่ หอมหวานคลาสสิก",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Strawberry_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Strawberry Banana",
                "description": "Cartridge รสสตรอเบอร์รี่กล้วย หอมหวานพิเศษ",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Strawberry Banana_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Watermelon Ice",
                "description": "Cartridge รสแตงโมเย็นฉ่ำ สดชื่นมาก",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Watermelon Ice_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Watermelon Lime",
                "description": "Cartridge รสแตงโมไลม์ หอมเปรี้ยวสดชื่น",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Watermelon Lime_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch Yogurt",
                "description": "Cartridge รสโยเกิร์ต หอมนุ่มนวล",
                "price": 19.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/ESKOBAR_Switch_Yogurt_Cartridge_ADs.jpg",
            },
            {
                "name": "Esko Switch 15 Flavors Collection",
                "description": "คอลเลกชั่น cartridge 15 รสชาติครบครัน",
                "price": 249.99,
                "category": "Starter Kit",
                "image_url": "/brands/esko/15-flavors-collection.jpg",
            },
            # Pikka Pod products
            {
                "name": "Pikka Pod System",
                "description": "Pod ระบบปิดพร้อมรสชาติพรีเมียม - อุปกรณ์พกพาสะดวก",
                "price": 59.99,
                "category": "Pod",
                "image_url": "/brands/pikka/system.png",
            },
            {
                "name": "Pikka Pod Apple Aloe",
                "description": "Pod รสแอปเปิ้ลอะลัว สดชื่นจากธรรมชาติ",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_APPLE ALOE.png",
            },
            {
                "name": "Pikka Pod Banana Milk",
                "description": "Pod รสกล้วยนม หอมหวานนุ่มนวล",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_BANANA MILK.png",
            },
            {
                "name": "Pikka Pod Blueberry Ice",
                "description": "Pod รสบลูเบอร์รี่เย็นฉ่ำ สดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_BLUEBERRY ICE.png",
            },
            {
                "name": "Pikka Pod Fanta Strawberry",
                "description": "Pod รสแฟนต้าสตรอเบอร์รี่ หอมหวาน",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_FANTA STRAWBERRY.png",
            },
            {
                "name": "Pikka Pod Grapes",
                "description": "Pod รสองุ่น หอมหวานจากธรรมชาติ",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_GRAPES.png",
            },
            {
                "name": "Pikka Pod Ice Chrysanthemum Tea",
                "description": "Pod รสชาดอกเบญจมาศเย็นฉ่ำ สดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_ICE CHRYSANTHEMUM TEA.png",
            },
            {
                "name": "Pikka Pod Lemon Cola",
                "description": "Pod รสเลมอนโคล่า หอมเปรี้ยวสดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_LEMON COLA.png",
            },
            {
                "name": "Pikka Pod Lychee",
                "description": "Pod รสลิ้นจี่ หอมหวานอร่อย",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_LYCHEE.png",
            },
            {
                "name": "Pikka Pod Mixed Berry",
                "description": "Pod รสเบอร์รี่รวม หอมหวานหลากสีสัน",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_MIXED BERRY.png",
            },
            {
                "name": "Pikka Pod Peach Strawberry",
                "description": "Pod รสพีชสตรอเบอร์รี่ หอมหวานนุ่มนวล",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_PEACH STRAWBERRY.png",
            },
            {
                "name": "Pikka Pod Pineapple Ice",
                "description": "Pod รสสับปะรดเย็นฉ่ำ สดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_PINEAPPLE ICE.png",
            },
            {
                "name": "Pikka Pod Pink Guava",
                "description": "Pod รสฝรั่งชมพู่ หอมหวานอร่อย",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_PINK GUAVA.png",
            },
            {
                "name": "Pikka Pod Sour Apple",
                "description": "Pod รสแอปเปิ้ลเปรี้ยว หอมสดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_SOUR APPLE.png",
            },
            {
                "name": "Pikka Pod Southern Peach Tea",
                "description": "Pod รสชาพีชภาคใต้ หอมหวานนุ่มนวล",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_SOUTHRN PEACH TEA.png",
            },
            {
                "name": "Pikka Pod Strawberry Banana",
                "description": "Pod รสสตรอเบอร์รี่กล้วย หอมหวานอร่อย",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_STRAWBERRY BANANA.png",
            },
            {
                "name": "Pikka Pod Strawberry Melo",
                "description": "Pod รสสตรอเบอร์รี่เมล่อน หอมหวานสดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_STRAWBERRY WATERMELON.png",
            },
            {
                "name": "Pikka Pod Watermelon Ice",
                "description": "Pod รสแตงโมเย็นฉ่ำ สดชื่นมาก",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod Flavor_WATERMELON ICE.png",
            },
            {
                "name": "Pikka Pod Cola Ice",
                "description": "Pod รสโคล่าเย็นฉ่ำ หอมสดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod_Flavor Box_COLA ICE.png",
            },
            {
                "name": "Pikka Pod Lemon Mint",
                "description": "Pod รสเลมอนมิ้นต์ หอมสดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod_Flavor Box_LEMON MINT RED DUST.png",
            },
            {
                "name": "Pikka Pod Red Dust",
                "description": "Pod รสแดงดัสต์ หอมหวานพิเศษ",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod_Flavor Box_LEMON MINT RED DUST.png",
            },
            {
                "name": "Pikka Pod Super Menthol",
                "description": "Pod รสซูเปอร์เมนธอล หอมเย็นสดชื่น",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod_Flavor Box_SUPERMENTHOL.png",
            },
            {
                "name": "Pikka Pod Watermelon Lychee",
                "description": "Pod รสแตงโมลิ้นจี่ หอมหวานอร่อย",
                "price": 14.99,
                "category": "Pod",
                "image_url": "/brands/pikka/Pikka Pod_Flavor Box_WATERMELON LYCHEE.png",
            },
            # Vortex Pro products
            {
                "name": "Vortex Pro Device",
                "description": "อุปกรณ์สูบไอระดับพรีเมียม Vortex Pro - ประสิทธิภาพสูงและทนทาน",
                "price": 89.99,
                "category": "Device",
                "image_url": "/brands/vortex/vortex-pro-device.jpg",
            },
            {
                "name": "Vortex Pro Starter Kit Complete",
                "description": "ชุดเริ่มต้น Vortex Pro - รวมอุปกรณ์และ pod ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/starter-kit-complete.jpg",
            },
            # Vortex Pro Prefill Pods (14 flavors)
            {
                "name": "Vortex Pro Pod Flavor 01",
                "description": "Pod Vortex Pro รสชาติพิเศษ 01 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-01.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 02",
                "description": "Pod Vortex Pro รสชาติพิเศษ 02 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-02.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 03",
                "description": "Pod Vortex Pro รสชาติพิเศษ 03 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-03.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 04",
                "description": "Pod Vortex Pro รสชาติพิเศษ 04 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-04.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 05",
                "description": "Pod Vortex Pro รสชาติพิเศษ 05 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-05.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 06",
                "description": "Pod Vortex Pro รสชาติพิเศษ 06 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-06.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 07",
                "description": "Pod Vortex Pro รสชาติพิเศษ 07 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-07.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 08",
                "description": "Pod Vortex Pro รสชาติพิเศษ 08 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-08.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 09",
                "description": "Pod Vortex Pro รสชาติพิเศษ 09 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-09.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 10",
                "description": "Pod Vortex Pro รสชาติพิเศษ 10 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-10.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 11",
                "description": "Pod Vortex Pro รสชาติพิเศษ 11 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-11.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 12",
                "description": "Pod Vortex Pro รสชาติพิเศษ 12 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-12.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 13",
                "description": "Pod Vortex Pro รสชาติพิเศษ 13 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-13.png",
            },
            {
                "name": "Vortex Pro Pod Flavor 14",
                "description": "Pod Vortex Pro รสชาติพิเศษ 14 - ประสบการณ์สูบไอพรีเมียม",
                "price": 24.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pod Individual-14.png",
            },
            # Vortex Pro Starter Kits (8 variants)
            {
                "name": "Vortex Pro Starter Kit 01",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 01 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-01.png",
            },
            {
                "name": "Vortex Pro Starter Kit 02",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 02 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-02.png",
            },
            {
                "name": "Vortex Pro Starter Kit 03",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 03 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-03.png",
            },
            {
                "name": "Vortex Pro Starter Kit 04",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 04 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-04.png",
            },
            {
                "name": "Vortex Pro Starter Kit 05",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 05 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-05.png",
            },
            {
                "name": "Vortex Pro Starter Kit 06",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 06 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-06.png",
            },
            {
                "name": "Vortex Pro Starter Kit 07",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 07 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-07.png",
            },
            {
                "name": "Vortex Pro Starter Kit 08",
                "description": "ชุดเริ่มต้น Vortex Pro รสชาติ 08 - รวมอุปกรณ์ครบครัน",
                "price": 129.99,
                "category": "Device",
                "image_url": "/brands/vortex/Vortex Pro Thailand INDIVIDUAL POST STARTER KIT-08.png",
            },
            # Additional products for variety
            {
                "name": "Game Theme Pod",
                "description": "Pod ธีมเกมสุดพิเศษ สำหรับเกมเมอร์ตัวยง",
                "price": 49.99,
                "category": "game",
            },
            {
                "name": "Premium Cleaning Kit",
                "description": "ชุดทำความสะอาดอุปกรณ์สูบไอครบครัน",
                "price": 15.99,
                "category": "Accessories",
            },
        ]

        # Add products to database
        for product_data in products_data:
            product = Product(**product_data)
            db.add(product)

        db.commit()

        # Verify products were added
        total_products = db.query(Product).count()
        products_by_category = {}
        for product in db.query(Product).all():
            category = product.category or "Uncategorized"
            if category not in products_by_category:
                products_by_category[category] = 0
            products_by_category[category] += 1

        print("✅ Database populated successfully!")
        print(f"📊 Total products added: {total_products}")
        print("📂 Products by category:")
        for category, count in products_by_category.items():
            print(f"   • {category}: {count} products")

        print("\n🎯 Brands with products:")
        print(
            f"   • Esko Switch: {products_by_category.get('Starter Kit', 0)} products"
        )
        print(f"   • Pikka Pod: {products_by_category.get('Pod', 0)} products")
        print(
            f"   • Vortex Pro: {products_by_category.get('Device', 0) + products_by_category.get('Accessories', 0)} products"
        )

    except Exception as e:
        print(f"❌ Error populating database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    populate_products()
