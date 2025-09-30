package com.priyanshu.password;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private static final String PREFS_NAME = "AppPrefs";
    private static final String KEY_PIN_SET = "pin_set";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button lockButton = findViewById(R.id.btn_lock);
        Button manageCardsButton = findViewById(R.id.btn_edit); // "Manage Cards" button
        Button resetPinButton = findViewById(R.id.btn_reset);

        lockButton.setOnClickListener(v -> lockApp());
        manageCardsButton.setOnClickListener(v -> showCardManagementMenu());
        resetPinButton.setOnClickListener(v -> resetPin());
    }

    private void showCardManagementMenu() {
        String[] options = {"Add", "Edit", "Delete"};
        new AlertDialog.Builder(this)
                .setTitle("Card Options")
                .setItems(options, (dialog, which) -> {
                    switch (which) {
                        case 0:
                            Toast.makeText(this, "Add selected", Toast.LENGTH_SHORT).show();
                            break;
                        case 1:
                            Toast.makeText(this, "Edit selected", Toast.LENGTH_SHORT).show();
                            break;
                        case 2:
                            Toast.makeText(this, "Delete selected", Toast.LENGTH_SHORT).show();
                            break;
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void lockApp() {
        Intent intent = new Intent(this, Lockscreen.class);
        startActivity(intent);
        finish();
    }

    private void resetPin() {
        new AlertDialog.Builder(this)
                .setTitle("Reset PIN")
                .setMessage("Are you sure you want to reset your PIN?")
                .setPositiveButton("Yes, Reset", (dialog, which) -> {
                    SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
                    prefs.edit()
                            .remove("pin_hash")
                            .putBoolean(KEY_PIN_SET, false)
                            .apply();
                    Toast.makeText(this, "PIN reset successfully!", Toast.LENGTH_SHORT).show();
                    lockApp();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }
}