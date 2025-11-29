Component Architecture: Functional Components Only

* Functional Components: All React components MUST be written as functional components.

* Hooks: All state and lifecycle events MUST be handled with React Hooks (useState, useEffect, useContext).

* Anti-Pattern (BLOCK): Class components (class ... extends Component) are forbidden for any new code.

* Exception: Class components are allowed ONLY for an ErrorBoundary (using componentDidCatch) until an equivalent functional version exists.