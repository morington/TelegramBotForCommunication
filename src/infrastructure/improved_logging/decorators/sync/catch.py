def catch_errors(exceptions=None, callback=None, **catch_kwargs):
    """
    Пример:
    @catch_errors(exceptions=(ValueError,), callback=handle) - Обрабатывает ValueError, иначе требует внешнего except
    @catch_errors(exceptions=(TypeError,), callback=handle) - Обрабатывает TypeError, иначе требует внешнего except
    @catch_errors(exceptions=(), callback=handle) - Всегда требует внешнего except
    @catch_errors(callback=handle) - Всегда обрабатывает все ошибки

    Можешь добавлять kwargs:
    @catch_errors(callback=handle, param=param, logger=logger)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_exception = False
                if exceptions is None:
                    handle_exception = True
                elif exceptions == ():
                    handle_exception = False
                elif isinstance(e, exceptions):
                    handle_exception = True

                if handle_exception:
                    if callback:
                        callback(e, **catch_kwargs)
                    # Исключение не пробрасывается дальше
                else:
                    raise  # Пробрасываем исключение дальше

        return wrapper

    return decorator
