from rest_framework_simplejwt.tokens import RefreshToken


def get_patient_token(patient):
    token = RefreshToken()
    token["patient_id"] = str(patient.id)
    token["email"] = patient.email
    token["type"] = "patient"
    return token
