<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Application architecture
- Keep shared navigation and frontend-only sample state in the Guardian provider and shell around the root Outlet so all screens share one session without suggesting backend persistence.
- Give each named screen its own TanStack file route and unique head metadata so navigation and deep links work consistently.
- Define all visual roles in src/styles.css and use shared design-system controls so the specification remains consistent across screens.
