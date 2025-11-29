# Jest Mocking Strategy (for TypeScript/JS)

* jest.mock('module-name', ...):
    * When to use: To mock an entire module or npm library (e.g., lodash, uuid, or an internal service).
    * Where: Must be called at the top level of the test file (outside of describe blocks).

* jest.spyOn(object, 'methodName'):
    * When to use: To spy on a method of an existing object to:
        * verify it was called,
        * or temporarily change/override its implementation for one specific test.
    * Where: Use this inside a beforeEach or inside a test block.

* Cleanup:
    * You MUST call:
        * jest.clearAllMocks()
        * OR jest.restoreAllMocks()
    * These must run in an afterEach block to ensure test isolation and prevent mock state from leaking between tests.