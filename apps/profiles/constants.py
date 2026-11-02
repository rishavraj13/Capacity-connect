"""Keep profile limits and write allowlists explicit."""

TEXT_MAX_LENGTH = 200
QUALIFICATION_YEAR_MIN = 1900
QUALIFICATION_YEAR_MAX = 2100
MIN_YEARS_EXPERIENCE = 0
MAX_YEARS_EXPERIENCE = 60
TRAINEE_FIELDS = ("bio", "interests", "photo")
TRAINER_FIELDS = ("bio", "headline", "years_experience", "photo")
QUALIFICATION_FIELDS = ("degree", "institution", "year")
EXPERIENCE_FIELDS = ("organisation", "role", "start_date", "end_date", "description")
CERTIFICATE_FIELDS = ("title", "issuer", "file", "issued_on")
ACCOUNT_FIELDS = ("first_name", "last_name", "email")
