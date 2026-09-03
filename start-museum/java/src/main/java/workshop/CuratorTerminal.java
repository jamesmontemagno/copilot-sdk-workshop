package workshop;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

public final class CuratorTerminal {
    private static final BufferedReader INPUT = new BufferedReader(new InputStreamReader(System.in));
    private static boolean closed;

    private CuratorTerminal() {
    }

    public static String askLine(String question) throws IOException {
        System.out.print(question);
        return readLine().trim();
    }

    public static boolean askYesNo(String question, boolean defaultYes) throws IOException {
        System.out.print(question + (defaultYes ? " [Y/n]: " : " [y/N]: "));
        String answer = readLine().trim();
        if (answer.isEmpty()) {
            return defaultYes;
        }
        if (answer.equalsIgnoreCase("y") || answer.equalsIgnoreCase("yes")) {
            return true;
        }
        if (answer.equalsIgnoreCase("n") || answer.equalsIgnoreCase("no")) {
            return false;
        }
        return defaultYes;
    }

    public static List<String> readFacts() throws IOException {
        System.out.println("Enter one approved fact per line. Submit a blank line when finished:");
        List<String> facts = new ArrayList<>();
        while (true) {
            String line = readLine();
            if (line.isBlank()) {
                break;
            }
            facts.add(line.trim());
        }
        return List.copyOf(facts);
    }

    public static void close() throws IOException {
        if (!closed) {
            closed = true;
            INPUT.close();
        }
    }

    private static String readLine() throws IOException {
        String line = INPUT.readLine();
        return line == null ? "" : line;
    }
}
