import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { LoginGate } from "@/components/LoginGate";
import { initialData, type BoardData } from "@/lib/kanban";

const fillLogin = async () => {
  await userEvent.type(screen.getByLabelText(/username/i), "user");
  await userEvent.type(screen.getByLabelText(/password/i), "password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

const addCard = async () => {
  const column = screen.getAllByTestId(/column-/i)[0];
  const addButton = screen.getAllByRole("button", { name: /add a card/i })[0];
  await userEvent.click(addButton);
  await userEvent.type(screen.getByPlaceholderText(/card title/i), "Stored card");
  await userEvent.click(screen.getByRole("button", { name: /add card/i }));
  return column;
};

describe("LoginGate", () => {
  let storedBoard: BoardData;

  beforeEach(() => {
    storedBoard = JSON.parse(JSON.stringify(initialData)) as BoardData;
    window.localStorage.clear();
    global.fetch = vi.fn(async (input, init) => {
      if (typeof input !== "string") {
        throw new Error("Unexpected fetch input");
      }

      if (input.includes("/api/ai/kanban")) {
        const payload = JSON.parse(init?.body as string) as {
          board: BoardData;
        };
        const updatedBoard = {
          ...payload.board,
          columns: payload.board.columns.map((column, index) =>
            index === 0 ? { ...column, title: "Inbox" } : column
          ),
        };
        return new Response(
          JSON.stringify({ response: "Updated the board.", board: updatedBoard }),
          { status: 200 }
        );
      }

      if (init?.method === "PUT") {
        storedBoard = JSON.parse(init.body as string) as BoardData;
        return new Response(JSON.stringify(storedBoard), { status: 200 });
      }

      return new Response(JSON.stringify(storedBoard), { status: 200 });
    }) as typeof fetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the login screen by default", () => {
    render(<LoginGate />);
    expect(screen.getByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
  });

  it("blocks invalid credentials", async () => {
    render(<LoginGate />);
    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "nope");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/invalid credentials/i);
  });

  it("allows login and logout", async () => {
    render(<LoginGate />);
    await fillLogin();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument()
    );
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(screen.getByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
  });

  it("keeps board changes after logout", async () => {
    render(<LoginGate />);
    await fillLogin();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument()
    );
    await addCard();
    expect(screen.getByText("Stored card")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    await fillLogin();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument()
    );
    expect(screen.getByText("Stored card")).toBeInTheDocument();
  });

  it("sends chat and applies updates", async () => {
    render(<LoginGate />);
    await fillLogin();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument()
    );

    await userEvent.type(screen.getByLabelText(/chat message/i), "Rename backlog");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() =>
      expect(screen.getByText("Updated the board.")).toBeInTheDocument()
    );
    expect(screen.getByDisplayValue("Inbox")).toBeInTheDocument();
  });
});
