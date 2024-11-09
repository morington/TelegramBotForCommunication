def catch_errors_async(exceptions=None, callback=None, **catch_kwargs):
    """
    Пример:
    @catch_errors_async(exceptions=(ValueError,), callback=handle) - Обрабатывает ValueError, иначе требует внешнего except
    @catch_errors_async(exceptions=(TypeError,), callback=handle) - Обрабатывает TypeError, иначе требует внешнего except
    @catch_errors_async(exceptions=(), callback=handle) - Всегда требует внешнего except
    @catch_errors_async(callback=handle) - Всегда обрабатывает все ошибки

    Можешь добавлять kwargs:
    @catch_errors_async(callback=handle, param=param, logger=logger)
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
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
                        callback(e, catch_kwargs)
                    # Исключение не пробрасывается дальше
                else:
                    raise  # Пробрасываем исключение дальше

        return wrapper

    return decorator
