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
                if exceptions is None or isinstance(e, exceptions):
                    if callback:
                        self = args[0]  # Предполагаем, что первый аргумент — это self
                        callback(self, e, **catch_kwargs)
                    # Не пробрасываем исключение дальше
                else:
                    raise  # Пробрасываем исключение дальше

        return wrapper

    return decorator
