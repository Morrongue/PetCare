def user_context(request):
    return {
        "username": request.session.get("user"),
        "rol": request.session.get("rol"),
    }
