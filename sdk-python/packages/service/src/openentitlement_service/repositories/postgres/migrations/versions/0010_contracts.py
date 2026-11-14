"""Private Product contract metadata and bounded PDF storage."""
import sqlalchemy as sa
from alembic import op
from openentitlement_service.repositories.postgres import rls

revision = "0010_contracts"
down_revision = "0009_merge_audit_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("entry", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contracts")),
        sa.UniqueConstraint("workspace_id", "id", name=op.f("uq_contracts_workspace_id_id")),
        sa.ForeignKeyConstraint(["workspace_id", "product_id"], ["products.workspace_id", "products.id"],
                                name=op.f("fk_contracts_workspace_id_products"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id", "organization_id"], ["organizations.workspace_id", "organizations.key"],
                                name=op.f("fk_contracts_workspace_id_organizations"), ondelete="CASCADE"),
    )
    op.create_table(
        "contract_documents",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("workspace_id", "contract_id", "id", name=op.f("pk_contract_documents")),
        sa.CheckConstraint("octet_length(content) <= 10485760", name=op.f("ck_contract_documents_bounded_pdf")),
        sa.ForeignKeyConstraint(["workspace_id", "contract_id"], ["contracts.workspace_id", "contracts.id"],
                                name=op.f("fk_contract_documents_workspace_id_contracts"), ondelete="CASCADE"),
    )
    for table in ("contracts", "contract_documents"):
        for statement in rls.enable(table, "workspace_id"):
            op.execute(statement)


def downgrade() -> None:
    op.drop_table("contract_documents")
    op.drop_table("contracts")
