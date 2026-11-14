"""Run with: uv run -m examples.constraints"""

from datetime import UTC, datetime
from typing import Self

from rakko import Field, MetaOption, Model, fields, meta, run_async
from rakko.context import RakkoContext
from rakko.exceptions import IntegrityError
from rakko.expressions import Criterion
from rakko.indexes import Index
from rakko.migrations.constraints import CheckConstraint, UniqueConstraint


class Stock(Model):
    """Declare metadata with @meta and register a check with a class method."""

    id: Field[int] = fields.AutoField(primary_key=True)
    warehouse: Field[str] = fields.CharField(100)
    sku: Field[str] = fields.CharField(100)
    quantity: Field[int] = fields.IntField(default=0)
    reserved: Field[int] = fields.IntField(default=0)

    # MetaOption accepts field objects directly in the model body.
    @meta
    class Meta(MetaOption):
        table = "stock"

    Meta.constraints = [
        UniqueConstraint(fields=(warehouse, sku), name="stock_warehouse_sku_unique")
    ]
    Meta.indexes = [Index(fields=(warehouse, quantity), name="stock_warehouse_quantity_idx")]

    # The callback receives the model class after its fields are initialized.
    @Meta.check_constraint
    @classmethod
    def stock_valid_quantities(cls) -> Criterion[Self]:
        return (cls.quantity >= 0) & (cls.reserved >= 0) & (cls.reserved <= cls.quantity)


class Product(Model):
    """Pass constraints and indexes directly to MetaOption(...)."""

    id: Field[int] = fields.AutoField(primary_key=True)
    category: Field[str] = fields.CharField(100)
    name: Field[str] = fields.CharField(100)
    price: Field[int] = fields.IntField()
    discount: Field[int] = fields.IntField(default=0)

    Meta = MetaOption(
        table="product",
        constraints=[
            CheckConstraint[Self](
                check=lambda model: (
                    (model.price >= 0) & (model.discount >= 0) & (model.discount <= model.price)
                ),
                name="product_valid_discount",
            ),
            UniqueConstraint(fields=(category, name), name="product_category_name_unique"),
        ],
        indexes=[Index(fields=(category, price), name="product_category_price_idx")],
    )


class Subscriber(Model):
    """Configure MetaOption() by assignment and declare conditional uniqueness.

    The conditional unique constraint requires PostgreSQL or SQLite.
    """

    id: Field[int] = fields.AutoField(primary_key=True)
    email: Field[str] = fields.CharField(254, source_field="email_address")
    deleted_at: Field[datetime | None] = fields.DatetimeField(null=True)

    Meta = MetaOption()
    Meta.table = "subscriber"
    Meta.indexes = [Index(fields=(deleted_at,), name="subscriber_deleted_at_idx")]

    # Deleted rows are excluded from the unique index, so their email can be reused.
    @Meta.unique_constraint(email)
    @classmethod
    def subscriber_active_email_unique(cls) -> Criterion[Self]:
        return cls.deleted_at.isnull()


async def run() -> None:
    async with RakkoContext() as context:
        await context.init(db_url="sqlite://:memory:", modules={"models": [__name__]})
        await context.generate_schemas()

        stock = await Stock.create(warehouse="Seoul", sku="RAKKO-001", quantity=10, reserved=2)
        # The same SKU is allowed in a different warehouse.
        await Stock.create(warehouse="Busan", sku="RAKKO-001", quantity=5)

        try:
            await Stock.create(warehouse="Seoul", sku="RAKKO-001", quantity=3)
        except IntegrityError:
            print("UniqueConstraint: duplicate warehouse/SKU rejected")
        else:
            raise AssertionError("Duplicate stock must violate the unique constraint")

        # CHECK constraints also apply to updates, not just inserts.
        try:
            await Stock.filter(Stock.id == stock.id).update(reserved=11)
        except IntegrityError:
            print("CheckConstraint: excess reservation rejected")
        else:
            raise AssertionError("Reservations must not exceed the quantity")

        # Filter by the leading index column and a range on the second column.
        print(
            "Available stock:",
            await Stock.filter((Stock.warehouse == "Seoul") & (Stock.quantity > 0)).values(
                Stock.sku, Stock.quantity, Stock.reserved
            ),
        )

        await Product.create(category="Books", name="Rakko guide", price=2000, discount=300)
        try:
            await Product.create(category="Books", name="Invalid offer", price=1000, discount=1500)
        except IntegrityError:
            print("Product: discount exceeding the price rejected")
        else:
            raise AssertionError("A discount must not exceed the price")
        print(
            "Products:",
            await Product.filter(Product.category == "Books").values(
                Product.name, Product.price, Product.discount
            ),
        )

        subscriber = await Subscriber.create(email="reader@example.com")
        try:
            await Subscriber.create(email="reader@example.com")
        except IntegrityError:
            print("Subscriber: duplicate active email rejected")
        else:
            raise AssertionError("Active subscribers must have unique emails")

        # Soft deletion releases the email without removing its history.
        await Subscriber.filter(Subscriber.id == subscriber.id).update(
            deleted_at=datetime(2026, 1, 1, tzinfo=UTC)
        )
        await Subscriber.create(email="reader@example.com")
        assert await Subscriber.all().count() == 2
        assert await Subscriber.filter(Subscriber.deleted_at.isnull()).count() == 1
        print("Subscriber: deleted email reused, history preserved")


if __name__ == "__main__":
    run_async(run())
