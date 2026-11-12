using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

// Лаунчер: рядом с exe лежит папка runtime (портативный Python 3.12)
// и файлы программы. Запускаем pythonw.exe app.py без окна консоли.
class Launcher
{
    [STAThread]
    static void Main()
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string pythonw = Path.Combine(dir, "runtime", "pythonw.exe");
        string app = Path.Combine(dir, "app.py");

        if (!File.Exists(pythonw))
        {
            MessageBox.Show(
                "Не найдена папка runtime рядом с программой.\n\n" +
                "Распакуй архив целиком и запускай BrelokQR.exe из распакованной папки — " +
                "один exe без папки не работает.",
                "Брелок с QR", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        if (!File.Exists(app))
        {
            MessageBox.Show(
                "Не найден app.py рядом с программой.\nРаспакуй архив целиком.",
                "Брелок с QR", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        try
        {
            ProcessStartInfo psi = new ProcessStartInfo(pythonw, "\"" + app + "\"");
            psi.WorkingDirectory = dir;
            psi.UseShellExecute = false;
            Process.Start(psi);
        }
        catch (Exception e)
        {
            MessageBox.Show("Не удалось запустить программу:\n" + e.Message,
                "Брелок с QR", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
