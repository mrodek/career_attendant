# State Management: Server vs. Client Separation

* Server and client state MUST be strictly separated.

## Server State

* Use TanStack Query (React Query) for:

    * all data fetching
    * caching
    * loading state
    * error handling
    * refetching

## Client State (Global)
* Use Zustand for global UI state such as:

    * theme
    * auth user object
    * any cross-component UI state

## Client State (Local)
* Use useState or useReducer for simple component-level state.

## Anti-Patterns (BLOCK):
* Do NOT use useEffect for data fetching — use useQuery().
* Do NOT use React Context for global state — causes unnecessary re-renders.
* Do NOT use Redux or Redux Toolkit (RTK) for new projects.