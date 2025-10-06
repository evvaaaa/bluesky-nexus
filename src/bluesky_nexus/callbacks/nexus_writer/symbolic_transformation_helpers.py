"""symbolic_transformation.py.

This module provides functionality for applying symbolic transformations to NumPy arrays
using dynamically evaluated mathematical expressions. It enables users to define complex
operations on arrays symbolically using Python syntax and NumPy functions.

Usage:
    Example usage of the module:

    >>> import numpy as np
    >>> from symbolic_transformation import apply_symbolic_transformation
    >>> array = np.array([1, 2, 3, 4])
    >>> expression = "3 * x**2 + np.sqrt(x)"
    >>> transformed_array = apply_symbolic_transformation(array, expression)
    >>> print(transformed_array)

Features:
    - Safe evaluation environment for symbolic expressions.
    - Support for mathematical operations with NumPy.
    - Flexible transformation logic defined at runtime.
"""

import numpy as np

from bluesky_nexus.common.logging_utils import logger


class ExpressionEvaluationError(ValueError):
    """ExpressionEvaluationError.

    Exception raised when an error occurs during the evaluation of an expression.

    This exception logs the provided error message immediately upon instantiation,
    and inherits from `ValueError`.

    Args:
        message (str): A description of the error that occurred during expression
        evaluation.
    """

    def __init__(self, message: str):
        """__init__.

        Initialize the ExpressionEvaluationError.

        Logs the error message upon creation and passes it to the base `ValueError`.

        Args:
            message (str): A description of the evaluation error.
        """
        # Log the exception as soon as it's created
        logger.exception(message)
        super().__init__(message)  # Call the base class constructor


def apply_symbolic_transformation(array: np.ndarray, expression: str) -> np.ndarray:
    """Apply a symbolic transformation to a NumPy array.

    Args:
        array (np.ndarray):
            The input NumPy array to be transformed. Each element of this array
            will be used as the variable `x` in the given expression.
        expression (str):
            A symbolic expression as a string where 'x' represents the array.
            The expression must follow Python syntax and can include valid NumPy
            functions (e.g., np.sqrt, np.exp, etc.).
            Examples:
                - '3 * x**2 + 5'
                - 'np.sqrt(x) + 10'
                - 'np.log(x) * np.exp(x)'

    Returns:
        np.ndarray:
            A NumPy array containing the result of applying the transformation
            to each element of the input array.

    Raises:
        ValueError:
            If the expression is invalid or cannot be evaluated safely within
            the provided environment.

    Example:
        >>> import numpy as np
        >>> array = np.array([1, 2, 3, 4])
        >>> expression = "3 * x**2 + 5"
        >>> apply_symbolic_transformation(array, expression)
        array([  8,  17,  32,  53])
    """
    # Define a safe evaluation environment

    # pylint: disable=too-few-public-methods
    class SafeNumpy:
        """Namespace for safe NumPy functions allowed.

        in symbolic expressions.
        """

        sqrt = np.sqrt
        exp = np.exp
        log = np.log
        sin = np.sin
        cos = np.cos

    safe_globals = {
        "__builtins__": None,
        # disables all dangerous built-in functions like open, eval, exec, import
        "np": SafeNumpy,
        # makes your custom safe subset of NumPy accessible to the expression
    }

    # 'x' represents the array in the expression
    x = array
    try:
        # Evaluate the expression in the restricted environment
        # pylint: disable=eval-used
        result = eval(expression, safe_globals, {"x": x})  # nosec
    except Exception as e:
        raise ExpressionEvaluationError(
            f"Failed to evaluate expression '{expression}'"
        ) from e

    return result
