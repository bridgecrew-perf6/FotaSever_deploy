from django.http import HttpResponse


def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            print(request)
            group = None
            print(request.user.username)
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
                if group in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponse("You are not Authorized to this page")
        return wrapper_func
    return decorator
