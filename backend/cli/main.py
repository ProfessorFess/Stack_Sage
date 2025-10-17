#!/usr/bin/env python3
"""
Stack Sage CLI - Your friendly MTG rules companion.

An intelligent Magic: The Gathering rules assistant powered by RAG.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.text import Text
from rich import box

from backend.core.rag_pipeline import graph


console = Console()


def print_banner():
    """Display the Stack Sage banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║               📘  STACK SAGE  📘                      ║
    ║                                                       ║
    ║        Your Intelligent MTG Rules Companion          ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print(
        "Powered by RAG • Comprehensive Rules • Scryfall API\n",
        style="dim italic",
        justify="center"
    )


def print_help():
    """Display help information."""
    help_text = """
    **How to Use Stack Sage:**
    
    • Ask questions about MTG rules and card interactions
    • Use quotes for card names: [cyan]"Rest in Peace"[/cyan]
    • Type [yellow]help[/yellow] to see this message
    • Type [yellow]examples[/yellow] to see example questions
    • Type [red]quit[/red] or [red]exit[/red] to leave
    
    **Tips:**
    • Be specific about card names
    • Ask about specific interactions
    • Reference multiple cards if needed
    """
    console.print(Panel(help_text, title="📖 Help", border_style="blue"))


def print_examples():
    """Display example questions."""
    examples = """
    **Example Questions:**
    
    1. What is the effect of "Rest in Peace"?
    2. How does "Dockside Extortionist" work with "Spark Double"?
    3. What happens when a player loses the game?
    4. How does the stack resolve?
    5. Does "Rest in Peace" stop Unearth?
    6. What is priority and how does it work?
    """
    console.print(Panel(examples, title="💡 Examples", border_style="green"))


def process_query(question: str) -> str:
    """
    Process a user query through the RAG pipeline.
    
    Args:
        question: User's question
        
    Returns:
        Generated answer
    """
    with console.status("[bold cyan]Thinking...", spinner="dots"):
        result = graph.invoke({"question": question})
        return result.get("response", "I couldn't generate an answer.")


def run_cli():
    """Main CLI loop."""
    print_banner()
    
    console.print(
        "💬 [bold]Ask me anything about Magic: The Gathering rules![/bold]\n",
        style="green"
    )
    console.print("Type [yellow]help[/yellow] for usage tips or [yellow]examples[/yellow] for sample questions.\n")
    
    while True:
        try:
            # Get user input
            # Don't use default="" to avoid prompt disappearing when text is deleted
            try:
                question = Prompt.ask(
                    "\n[bold cyan]🃏 Your question[/bold cyan]"
                )
            except EOFError:
                # Handle Ctrl+D gracefully
                console.print("\n\n[yellow]Goodbye! 👋[/yellow]\n")
                break
            
            # Handle empty input
            if not question or not question.strip():
                continue
            
            # Handle special commands
            command = question.lower().strip()
            
            if command in ["quit", "exit", "q"]:
                console.print("\n[yellow]Thanks for using Stack Sage! May your draws be blessed! ✨[/yellow]\n")
                break
            
            elif command == "help":
                print_help()
                continue
            
            elif command == "examples":
                print_examples()
                continue
            
            elif command == "clear":
                console.clear()
                print_banner()
                continue
            
            # Process the question
            console.print()  # Add spacing
            
            answer = process_query(question)
            
            # Display the answer in a nice panel
            console.print(
                Panel(
                    Markdown(answer),
                    title="📜 Answer",
                    border_style="green",
                    box=box.ROUNDED
                )
            )
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted! Type 'quit' to exit.[/yellow]")
            continue
        
        except Exception as e:
            console.print(f"\n[red]❌ Error:[/red] {str(e)}\n")
            console.print("[dim]Please try again or type 'help' for assistance.[/dim]")


def main():
    """Entry point for the CLI."""
    try:
        run_cli()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Goodbye! 👋[/yellow]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error:[/red] {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
