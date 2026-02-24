import re

content = open(
    r"d:\Tech\odoo-19.0+e.20250918\custom_addons_project2\trasas_asset_management\views\asset_views.xml",
    "r",
    encoding="utf-8",
).read()
view_fields = set(re.findall(r'<field\s+name="(\w+)"', content))

py_content = open(
    r"d:\Tech\odoo-19.0+e.20250918\custom_addons_project2\trasas_asset_management\models\asset.py",
    "r",
    encoding="utf-8",
).read()
model_fields = set(re.findall(r"(\w+)\s*=\s*fields\.", py_content))

inherited = {
    "message_ids",
    "message_follower_ids",
    "activity_ids",
    "activity_state",
    "activity_user_id",
    "activity_type_id",
    "activity_date_deadline",
    "activity_summary",
    "website_message_ids",
    "message_attachment_count",
    "message_main_attachment_id",
    "active",
}
model_fields.update(inherited)

exclude = {"name", "model", "arch", "button_box", "handle", "sequence", "string"}
missing = view_fields - model_fields - exclude

print("Fields in view but not in model:")
for f in sorted(missing):
    print(f"  - {f}")
print(f"\nTotal: {len(missing)} missing fields")
print(f"\nAll view fields: {sorted(view_fields)}")
