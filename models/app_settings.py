from extensions import db


class AppSettings(db.Model):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    theme = db.Column(db.String(20), nullable=False, default="light")
    sticky_navbar = db.Column(db.Boolean, nullable=False, default=True)
    pagination_enabled = db.Column(db.Boolean, nullable=False, default=True)
    pagination_size = db.Column(db.Integer, nullable=False, default=25)
    back_to_top = db.Column(db.Boolean, nullable=False, default=True)

    @staticmethod
    def get():
        """Return the singleton settings row, auto-creating if missing."""
        settings = db.session.get(AppSettings, 1)
        if not settings:
            settings = AppSettings(
                id=1,
                theme="light",
                sticky_navbar=True,
                pagination_enabled=True,
                pagination_size=25,
                back_to_top=True,
            )
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self):
        return f"<AppSettings theme={self.theme}>"
