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
                if exceptions is None or isinstance(e, exceptions):
                    if callback:
                        self = args[0]  # Предполагаем, что первый аргумент — это self
                        await callback(self, e, **catch_kwargs)
                    # Не пробрасываем исключение дальше
                else:
                    raise  # Пробрасываем исключение дальше

        return wrapper

    return decorator
