package com.priyanshu.password;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;
import android.widget.ArrayAdapter;
import android.widget.TextView;
import android.view.View;
import android.view.ViewGroup;

import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;

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
                            showAddPasswordDialog();
                            break;
                        case 1:
                            Toast.makeText(this, "Edit selected (not implemented yet)", Toast.LENGTH_SHORT).show();
                            break;
                        case 2:
                            Toast.makeText(this, "Delete selected (not implemented yet)", Toast.LENGTH_SHORT).show();
                            break;
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void showAddPasswordDialog() {
        // Create a vertical layout for input fields
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        EditText etAppName = new EditText(this);
        etAppName.setHint("App/Website Name");
        layout.addView(etAppName);

        EditText etUsername = new EditText(this);
        etUsername.setHint("Username/Email");
        layout.addView(etUsername);

        EditText etPassword = new EditText(this);
        etPassword.setHint("Password");
        etPassword.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        layout.addView(etPassword);

        new AlertDialog.Builder(this)
                .setTitle("Add Password")
                .setView(layout)
                .setPositiveButton("Add", (dialog, which) -> {
                    String appName = etAppName.getText().toString().trim();
                    String username = etUsername.getText().toString().trim();
                    String password = etPassword.getText().toString().trim();

                    if (!appName.isEmpty() && !username.isEmpty() && !password.isEmpty()) {
                        addCard(appName, username, password);
                    } else {
                        Toast.makeText(this, "All fields required", Toast.LENGTH_SHORT).show();
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void addCard(String appName, String username, String password) {
        // Create CardView
        CardView cardView = new CardView(this);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, 0, 0, 24); // spacing between cards
        cardView.setLayoutParams(params);
        cardView.setRadius(16f);
        cardView.setCardElevation(8f);
        cardView.setUseCompatPadding(true);

        // Inner layout
        LinearLayout innerLayout = new LinearLayout(this);
        innerLayout.setOrientation(LinearLayout.VERTICAL);
        innerLayout.setPadding(32, 32, 32, 32);

        // Title
        TextView tvAppName = new TextView(this);
        tvAppName.setText(appName);
        tvAppName.setTextSize(18);
        tvAppName.setTypeface(null, Typeface.BOLD);
        innerLayout.addView(tvAppName);

        // Username
        TextView tvUsername = new TextView(this);
        tvUsername.setText("Username: " + username);
        innerLayout.addView(tvUsername);

        // Password
        TextView tvPassword = new TextView(this);
        tvPassword.setText("Password: " + password);
        innerLayout.addView(tvPassword);

        // Add inner layout to card
        cardView.addView(innerLayout);

        // Finally add card to container
        LinearLayout container = findViewById(R.id.cards_container);
        container.addView(cardView);
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
                    lockApp();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }
}
