import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Scanner;

public class GradesReport {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        System.out.print("Enter number of students: ");
        int count = Integer.parseInt(scanner.nextLine().trim());
        if (count <= 0) {
            System.out.println("No students to process. Exiting.");
            scanner.close();
            return;
        }

        String[] names = new String[count];
        double[] grades = new double[count];

        for (int i = 0; i < count; i++) {
            System.out.printf("%nEnter name of student %d: ", i + 1);
            names[i] = scanner.nextLine().trim();
            System.out.printf("Enter grade of %s: ", names[i]);
            while (true) {
                try {
                    grades[i] = Double.parseDouble(scanner.nextLine().trim());
                    break;
                } catch (NumberFormatException e) {
                    System.out.print("Invalid grade. Re-enter: ");
                }
            }
        }

        int passed = countPassed(grades);
        try {
            writeToFile(names, grades, passed);
            System.out.println("\nReport generated: GradesReport.txt");
        } catch (IOException e) {
            System.out.println("Failed to write report: " + e.getMessage());
        }

        scanner.close();
    }

    public static int countPassed(double[] grades) {
        int passed = 0;
        for (double grade : grades) {
            if (grade >= 75.0) {
                passed++;
            }
        }
        return passed;
    }

    public static void writeToFile(String[] names, double[] grades, int passed) throws IOException {
        int failed = names.length - passed;
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("GradesReport.txt"))) {
            writer.write("Student Grades:\n");
            for (int i = 0; i < names.length; i++) {
                writer.write(String.format("%s - %.1f%n", names[i], grades[i]));
            }
            writer.newLine();
            writer.write("Passed: " + passed + System.lineSeparator());
            writer.write("Failed: " + failed + System.lineSeparator());
        }
    }
}
