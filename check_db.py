#!/usr/bin/env python3
"""
Check database connection and current products
"""
import sys

sys.path.append(".")

try:
    from app.main import Base, Product, SessionLocal, engine

    # Create tables if needed
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check current products
        products = db.query(Product).all()
        print(f"📊 Current products in database: {len(products)}")

        if len(products) == 0:
            print("⚠️  No products found. Adding sample products...")

            # Add sample products
            sample_products = [
                Product(
                    name="Esko Switch Starter Kit",
                    description="Starter Kit และ Cartridge หลากหลายรสชาติ",
                    price=79.99,
                    category="Starter Kit",
                ),
                Product(
                    name="Pikka Pod System",
                    description="Pod ระบบปิดพร้อมรสชาติพรีเมียม",
                    price=59.99,
                    category="Pod",
                ),
                Product(
                    name="Vortex Pro Device",
                    description="อุปกรณ์สูบไอระดับพรีเมียม",
                    price=129.99,
                    category="Device",
                ),
                Product(
                    name="Game Theme Pod",
                    description="Pod ธีมเกมสุดพิเศษ",
                    price=49.99,
                    category="game",
                ),
                Product(
                    name="Premium Cleaning Kit",
                    description="ชุดทำความสะอาดอุปกรณ์สูบไอครบครัน",
                    price=15.99,
                    category="Accessories",
                ),
            ]

            for product in sample_products:
                db.add(product)

            db.commit()
            print("✅ Sample products added successfully!")

        # Show final count
        final_count = db.query(Product).count()
        print(f"📈 Final product count: {final_count}")

        # Show products by category
        from sqlalchemy import func

        category_counts = (
            db.query(Product.category, func.count(Product.id))
            .group_by(Product.category)
            .all()
        )

        print("\n📂 Products by category:")
        for category, count in category_counts:
            print(f"   • {category or 'Uncategorized'}: {count} products")

    except Exception as e:
        print(f"❌ Database error: {e}")
        db.rollback()
    finally:
        db.close()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
