package com.priyanshu.password;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import android.widget.ArrayAdapter;
import android.widget.TextView;
import android.view.View;
import android.view.ViewGroup;

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
        // Define items and corresponding built-in icons
        String[] items = {"Add Password", "Edit Password", "Delete Password"};
        int[] icons = {
                android.R.drawable.ic_menu_add,
                android.R.drawable.ic_menu_edit,
                android.R.drawable.ic_menu_delete
        };

        // Create a simple list adapter
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.select_dialog_item, android.R.id.text1, items) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                View view = super.getView(position, convertView, parent);
                TextView textView = (TextView) view.findViewById(android.R.id.text1);

                // Set compound drawable (icon on left)
                textView.setCompoundDrawablesWithIntrinsicBounds(icons[position], 0, 0, 0);
                textView.setCompoundDrawablePadding(24); // space between icon and text

                // Optional: Make "Delete" red
                if (position == 2) {
                    textView.setTextColor(getColor(android.R.color.holo_red_dark));
                } else {
                    textView.setTextColor(getColor(android.R.color.primary_text_dark)); // or use your theme color
                }

                return view;
            }
        };

        new AlertDialog.Builder(this)
                .setTitle("Card Options")
                .setAdapter(adapter, (dialog, which) -> {
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