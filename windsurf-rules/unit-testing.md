# Unit Testing: Quality, Structure, and Naming
1. Test Structure: Arrange–Act–Assert (AAA)

    * All tests MUST follow the AAA pattern.
    * Arrange: Prepare all inputs, mocks, and preconditions.
    * Act: Execute a single function/method under test.
    * Assert: Validate outputs, side effects, and mock interactions.
    * Anti-Pattern (BLOCK): Do NOT perform multiple actions/assertions in one test. Each action requires its own test.

2. Test Naming: "Given–When–Then" Convention

    * Tests MUST use descriptive names in the format:
        * it('Given_[Precondition]_When_[Action]_Then_[Outcome]')
    * Example:
        * it('Given_UserIsUnauthenticated_When_AccessingProfile_Then_RedirectsToLogin')
    * Anti-Pattern (BLOCK): Do NOT use vague test names such as:
        * it('should work')
        * it('test profile')